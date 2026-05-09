CREATE VIEW IF NOT EXISTS delivery_analytics.delivery_cost_total_view AS
SELECT
    sum(delivery_cost_rub) AS total_delivery_cost_rub
FROM delivery_analytics.delivery_cost_calculations;


CREATE VIEW IF NOT EXISTS delivery_analytics.delivery_cost_max_view AS
SELECT
    max(delivery_cost_rub) AS max_delivery_cost_rub
FROM delivery_analytics.delivery_cost_calculations;


CREATE VIEW IF NOT EXISTS delivery_analytics.delivery_cost_min_view AS
SELECT
    min(delivery_cost_rub) AS min_delivery_cost_rub
FROM delivery_analytics.delivery_cost_calculations;
