from fastapi import APIRouter

from resume_classifier import __version__
from resume_classifier.schemas import VersionResponse

router = APIRouter(tags=["service"])


@router.get("/version")
async def version() -> VersionResponse:
    return VersionResponse(version=__version__)
