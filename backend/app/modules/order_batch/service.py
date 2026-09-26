"""多墙合并订卷：同一卷材对多面墙分别测算，回包分墙明细与合计 rolls。

与单墙测算服务（app.services.estimate_service）分模块；
每面墙仍走 app.engines.wallpaper_math.roll_count 现有算法，合计为分墙卷数之和。
"""

from fastapi import HTTPException

from app.engines.wallpaper_math import roll_count
from app.repositories import history, rolls, walls


def run_batch_estimate(wall_ids, roll_id: int, save: bool, note: str = ""):
    # 去重保序；空列表直接失败，不产生任何行
    ids = list(dict.fromkeys(int(w) for w in (wall_ids or [])))
    if not ids:
        raise HTTPException(422, "wall_ids must not be empty")

    roll = rolls.get_roll(roll_id)
    if not roll:
        raise HTTPException(404, "roll not found")
    if roll.get("data_quality") == "dirty":
        raise HTTPException(422, "dirty seed entity")

    # 先校验全部墙面，再统一测算：任何一面缺失或 dirty 都整体失败，不落库、不增行
    wall_rows = []
    for wid in ids:
        wall = walls.get_wall(wid)
        if not wall:
            raise HTTPException(404, f"wall {wid} not found")
        if wall.get("data_quality") == "dirty":
            raise HTTPException(422, "dirty seed entity")
        wall_rows.append(wall)

    items = []
    for wall in wall_rows:
        calc = roll_count(
            wall["perimeter"], wall["height"], roll["width"], roll["length"], roll["pattern_cm"]
        )
        items.append({"wall_id": wall["id"], "wall_name": wall["name"], **calc})

    total_rolls = sum(i["rolls"] for i in items)
    total_drops = sum(i["drops"] for i in items)

    result = {
        "kind": "order_batch",
        "roll_id": roll_id,
        "wall_ids": [w["id"] for w in wall_rows],
        "items": items,
        "drops": total_drops,
        "rolls": total_rolls,
    }
    run_id = None
    if save:
        # 落库只写一条 run：分墙明细快照存入 result_json，之后改墙数据不重算
        run_id = history.insert_run(None, roll_id, result, note)
    return {
        "walls": wall_rows,
        "roll": roll,
        "run_id": run_id,
        "items": items,
        "drops": total_drops,
        "rolls": total_rolls,
    }
