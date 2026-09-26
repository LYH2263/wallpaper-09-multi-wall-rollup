from pydantic import BaseModel


class EstimateRequest(BaseModel):
    wall_id: int
    roll_id: int
    save: bool = False
    note: str = ""


class OrderBatchRequest(BaseModel):
    wall_ids: list[int]
    roll_id: int
    save: bool = False
    note: str = ""
