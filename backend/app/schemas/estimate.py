from pydantic import BaseModel, Field


class EstimateRequest(BaseModel):
    wall_id: int
    roll_id: int
    save: bool = False
    note: str = ""


class BatchEstimateRequest(BaseModel):
    wall_ids: list[int] = Field(..., min_length=1)
    roll_id: int
    save: bool = False
    note: str = ""
