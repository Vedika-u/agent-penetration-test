import uvicorn

from target_agent.config import settings


def main() -> None:
    uvicorn.run("target_agent.api:app", host="0.0.0.0", port=settings.api_port)


if __name__ == "__main__":
    main()
