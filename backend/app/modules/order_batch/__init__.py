"""Multi-wall order batch aggregation.

Pure summarisation: every wall is calculated independently with the same
single-wall engine (``app.engines.wallpaper_math.roll_count``); this module
only fans the calculation out and sums the per-wall results. It never reaches
into the database or HTTP layer, and it deliberately does not merge walls
before calculating (each wall keeps its own drops/rolls).
"""

from app.engines.wallpaper_math import roll_count


def _wall_calc(wall: dict, roll: dict) -> dict:
    calc = roll_count(
        wall["perimeter"], wall["height"], roll["width"], roll["length"], roll["pattern_cm"]
    )
    # Snapshot of the inputs at calculation time, so a saved run stays fixed
    # even if the wall's perimeter (or the roll) is edited afterwards.
    return {
        "wall_id": wall["id"],
        "wall_name": wall["name"],
        "perimeter": wall["perimeter"],
        "height": wall["height"],
        "drops": calc["drops"],
        "drop_len_m": calc["drop_len_m"],
        "strips_per_roll": calc["strips_per_roll"],
        "rolls": calc["rolls"],
        "calc": calc,
    }


def aggregate(walls: list[dict], roll: dict) -> dict:
    """Calculate each wall separately against the same roll and total the rolls.

    The per-wall total of a single-element batch is therefore identical to a
    standalone single-wall estimate.
    """
    items = [_wall_calc(w, roll) for w in walls]
    return {
        "items": items,
        "totals": {
            "wall_count": len(items),
            "drops": sum(i["drops"] for i in items),
            "rolls": sum(i["rolls"] for i in items),
        },
    }
