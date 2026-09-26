from fastapi import APIRouter
from app.schemas.estimate import OrderBatchRequest
from app.services import order_batch_service

router = APIRouter()


@router.post("/order-batch/estimate")
def order_batch_estimate(body: OrderBatchRequest):
    return order_batch_service.run_batch(body.wall_ids, body.roll_id, body.save, body.note)
