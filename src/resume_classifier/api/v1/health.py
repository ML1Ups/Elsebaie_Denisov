from fastapi import APIRouter, Request, Response, status

from resume_classifier.checks import collect_health
from resume_classifier.schemas import HealthResponse

router = APIRouter(tags=["service"])


@router.get(
    "/health",
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": HealthResponse}},
)
async def health(request: Request, response: Response) -> HealthResponse:
    result = await collect_health(
        request.app.state.db_pool,
        request.app.state.settings.health_check_timeout_seconds,
    )
    if result.status != "ok":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return result
