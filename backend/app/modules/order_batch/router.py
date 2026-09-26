from fastapi import APIRouter

from app.modules.order_batch import run_batch_estimate
from app.schemas.estimate import BatchEstimateRequest

router = APIRouter()


@router.post("/estimate/batch")
def estimate_batch_post(body: BatchEstimateRequest):
    return run_batch_estimate(body.wall_ids, body.roll_id, body.save, body.note)
