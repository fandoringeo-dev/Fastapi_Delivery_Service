CREATE TABLE IF NOT EXISTS delivery_cost_calculations
(
    parcel_id String,
    parcel_type_id UInt32,
    parcel_type_name String,
    weight_kg Decimal(10, 3),
    declared_value_usd Decimal(12, 2),
    usd_to_rub_rate Decimal(12, 4),
    delivery_cost_rub Decimal(12, 2),
    calculated_at DateTime
)
ENGINE = MergeTree
ORDER BY (calculated_at, parcel_id);
