import asyncio

from app.workers.parcel_worker import run_parcel_worker


def main() -> None:
    """
    Запускает worker обработки посылок.
    """
    asyncio.run(run_parcel_worker())


if __name__ == "__main__":
    main()
