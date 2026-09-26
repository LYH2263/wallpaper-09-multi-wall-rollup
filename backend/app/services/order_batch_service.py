"""Multi-wall order batch estimate service.

Separate from ``estimate_service`` (single wall). Validation of every wall and
the shared roll happens before any write, so a rejected request (empty list,
missing entity, dirty entity) never creates a run. Saving writes exactly one
``calc_runs`` row whose result JSON holds per-wall details plus the totals; the
per-wall snapshots make the saved batch immune to later wall edits.
"""

from fastapi import HTTPException

from app.modules.order_batch import aggregate
from app.repositories import history, rolls, walls


def run_batch(wall_ids: list[int], roll_id: int, save: bool, note: str):
    if not wall_ids:
        raise HTTPException(422, "wall_ids must not be empty")

    roll = rolls.get_roll(roll_id)
    if not roll:
        raise HTTPException(404, "roll not found")
    if roll.get("data_quality") == "dirty":
        raise HTTPException(422, "dirty seed entity")

    # De-duplicate while keeping order; validate everything up front.
    selected = []
    seen = set()
    for wid in wall_ids:
        if wid in seen:
            continue
        seen.add(wid)
        wall = walls.get_wall(wid)
        if not wall:
            raise HTTPException(404, f"wall {wid} not found")
        if wall.get("data_quality") == "dirty":
            raise HTTPException(422, "dirty seed entity")
        selected.append(wall)

    batch = aggregate(selected, roll)

    run_id = None
    if save:
        payload = {"kind": "order_batch", "roll_id": roll_id, "roll_name": roll["name"], **batch}
        # One run for the whole batch; wall_id stays NULL, the per-wall details
        # live inside result_json.
        run_id = history.insert_run(None, roll_id, payload, note)

    return {"walls": selected, "roll": roll, "run_id": run_id, **batch}
