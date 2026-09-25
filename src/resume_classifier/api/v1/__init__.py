from fastapi import APIRouter

from resume_classifier.api.v1 import health, version

router = APIRouter(prefix="/api/v1")
router.include_router(version.router)
router.include_router(health.router)
