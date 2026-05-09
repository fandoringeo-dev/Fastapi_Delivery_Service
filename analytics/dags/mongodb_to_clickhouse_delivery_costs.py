from datetime import datetime
from decimal import Decimal

import clickhouse_connect
from airflow import DAG
from airflow.operators.python import PythonOperator
from pymongo import MongoClient

from analytics.config import analytics_settings


def load_delivery_cost_calculations_to_clickhouse() -> None:
    """
    Загружает логи расчета стоимости доставки из MongoDB в ClickHouse.
    """
    mongo_client = MongoClient(analytics_settings.mongodb_url)
    try:
        mongo_database = mongo_client[analytics_settings.mongodb_db]
        collection = mongo_database["delivery_cost_calculation_logs"]

        documents = list(collection.find())

        if not documents:
            return

        clickhouse_client = clickhouse_connect.get_client(
            host=analytics_settings.clickhouse_host,
            port=analytics_settings.clickhouse_port,
            username=analytics_settings.clickhouse_user,
            password=analytics_settings.clickhouse_password,
            database=analytics_settings.clickhouse_db,
        )

        existing_rows = clickhouse_client.query(
            "SELECT parcel_id, calculated_at FROM delivery_cost_calculations"
        ).result_rows
        existing_keys = set(existing_rows)

        rows = []
        for document in documents:
            calculated_at = document["calculated_at"].replace(microsecond=0)
            row_key = (document["parcel_id"], calculated_at)
            if row_key in existing_keys:
                continue

            rows.append(
                [
                    document["parcel_id"],
                    document["parcel_type_id"],
                    document["parcel_type_name"],
                    Decimal(document["weight_kg"]),
                    Decimal(document["declared_value_usd"]),
                    Decimal(document["usd_to_rub_rate"]),
                    Decimal(document["delivery_cost_rub"]),
                    document["calculated_at"],
                ]
            )
            existing_keys.add(row_key)

        if not rows:
            return

        clickhouse_client.insert(
            "delivery_cost_calculations",
            rows,
            column_names=[
                "parcel_id",
                "parcel_type_id",
                "parcel_type_name",
                "weight_kg",
                "declared_value_usd",
                "usd_to_rub_rate",
                "delivery_cost_rub",
                "calculated_at",
            ],
        )
    finally:
        mongo_client.close()



with DAG(
    dag_id="mongodb_to_clickhouse_delivery_costs",
    start_date=datetime(2026, 5, 7),
    schedule="@hourly",
    catchup=False,
) as dag:
    load_delivery_costs_task = PythonOperator(
        task_id="load_delivery_cost_calculations_to_clickhouse",
        python_callable=load_delivery_cost_calculations_to_clickhouse,
    )
