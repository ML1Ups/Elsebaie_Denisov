import uvicorn

from resume_classifier.config import get_settings
from resume_classifier.logs import configure_logging
from resume_classifier.main import create_app


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level, settings.log_json)
    uvicorn.run(
        create_app(settings),
        host=settings.app_host,
        port=settings.app_port,
        log_config=None,
        access_log=False,
    )


if __name__ == "__main__":
    main()
