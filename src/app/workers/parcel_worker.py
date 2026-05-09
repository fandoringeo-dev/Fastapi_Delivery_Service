import json
from uuid import UUID

from loguru import logger

from app.common.enums import ParcelStatus
from app.db.mongodb import get_mongodb_database
from app.db.rabbitmq import get_rabbitmq_connection
from app.db.redis import get_redis_client
from app.db.session import async_session_factory
from app.repositories.parcel import ParcelRepository
from app.services.calculation_log import CalculationLogService
from app.services.delivery_cost import DeliveryCostService
from app.services.exchange_rate import ExchangeRateService
from app.services.rabbitmq_producer import PARCELS_QUEUE_NAME


async def run_parcel_worker() -> None:
    """
    Запускает worker обработки посылок.
    """
    connection = await get_rabbitmq_connection()
    channel = await connection.channel()
    queue = await channel.declare_queue(PARCELS_QUEUE_NAME, durable=True)

    logger.info("Worker обработки посылок запущен. Ожидание сообщений...")

    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            async with message.process():
                payload = json.loads(message.body.decode("utf-8"))
                parcel_id = UUID(payload["parcel_id"])

                logger.info(
                    "Получено сообщение из очереди parcels: parcel_id={}",
                    parcel_id,
                )

                async with async_session_factory() as session:
                    repository = ParcelRepository(session)
                    parcel = await repository.get_parcel_by_id(parcel_id)

                    if parcel is None:
                        logger.warning(
                            "Посылка для обработки не найдена: parcel_id={}",
                            parcel_id,
                        )
                        continue

                    try:
                        redis_client = get_redis_client()
                        exchange_rate_service = ExchangeRateService(redis_client)
                        delivery_cost_service = DeliveryCostService()

                        usd_to_rub_rate = (
                            await exchange_rate_service.get_usd_to_rub_rate()
                        )

                        delivery_cost_rub = (
                            await delivery_cost_service.calculate_delivery_cost(
                                weight_kg=parcel.weight_kg,
                                declared_value_usd=parcel.declared_value_usd,
                                usd_to_rub_rate=usd_to_rub_rate,
                            )
                        )

                        parcel.delivery_cost_rub = delivery_cost_rub
                        parcel.status = ParcelStatus.PROCESSED

                        await session.commit()
                        await session.refresh(parcel)

                        logger.info(
                            "Посылка успешно обработана: parcel_id={}, status={}, delivery_cost_rub={}",
                            parcel.id,
                            parcel.status,
                            parcel.delivery_cost_rub,
                        )

                        mongodb_database = get_mongodb_database()
                        calculation_log_service = CalculationLogService(
                            mongodb_database
                        )

                        await calculation_log_service.create_log(
                            parcel=parcel,
                            usd_to_rub_rate=usd_to_rub_rate,
                        )

                        logger.info(
                            "Лог расчета стоимости доставки сохранен в MongoDB: parcel_id={}",
                            parcel.id,
                        )

                    except Exception:
                        await session.rollback()

                        parcel.status = ParcelStatus.FAILED
                        await session.commit()

                        logger.exception(
                            "Ошибка расчета стоимости посылки: parcel_id={}",
                            parcel_id,
                        )
