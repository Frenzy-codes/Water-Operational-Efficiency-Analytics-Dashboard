-- ─────────────────────────────────────────────────────────────────────────
-- analysis.sql
-- Water & Operational Efficiency Analytics Dashboard
-- Business Intelligence Queries — 12 analytical queries
-- ─────────────────────────────────────────────────────────────────────────

USE ecolab_analytics;

-- ═════════════════════════════════════════════════════════════════════════
-- QUERY 1: Total water consumption by plant (ranking)
-- Business question: Which plant consumes the most water?
-- ═════════════════════════════════════════════════════════════════════════
SELECT
    p.plant_name,
    p.location,
    p.plant_type,
    ROUND(SUM(w.water_consumption_liters) / 1000000, 2)   AS total_water_ML,
    ROUND(AVG(w.water_consumption_liters), 0)              AS avg_daily_liters,
    RANK() OVER (ORDER BY SUM(w.water_consumption_liters) DESC) AS consumption_rank
FROM fact_water_usage w
JOIN dim_plant p USING(plant_id)
GROUP BY p.plant_id, p.plant_name, p.location, p.plant_type
ORDER BY total_water_ML DESC;


-- ═════════════════════════════════════════════════════════════════════════
-- QUERY 2: Recycling performance by plant
-- Business question: How effectively is each plant recycling water?
-- ═════════════════════════════════════════════════════════════════════════
SELECT
    p.plant_name,
    ROUND(SUM(w.recycled_water_liters) / 1000000, 2)      AS total_recycled_ML,
    ROUND(SUM(w.water_consumption_liters) / 1000000, 2)   AS total_consumed_ML,
    ROUND(
        SUM(w.recycled_water_liters) /
        SUM(w.water_consumption_liters) * 100, 1
    )                                                       AS recycling_pct
FROM fact_water_usage w
JOIN dim_plant p USING(plant_id)
GROUP BY p.plant_id, p.plant_name
ORDER BY recycling_pct DESC;


-- ═════════════════════════════════════════════════════════════════════════
-- QUERY 3: Monthly water consumption trend (seasonality analysis)
-- Business question: Are there seasonal patterns in water usage?
-- ═════════════════════════════════════════════════════════════════════════
SELECT
    d.month_name,
    d.month,
    ROUND(SUM(w.water_consumption_liters) / 1000000, 2)   AS total_water_ML,
    ROUND(AVG(w.water_consumption_liters), 0)              AS avg_daily_liters,
    ROUND(SUM(w.recycled_water_liters) /
          SUM(w.water_consumption_liters) * 100, 1)        AS monthly_recycling_pct
FROM fact_water_usage w
JOIN dim_date d ON w.date = d.date_key
GROUP BY d.month, d.month_name
ORDER BY d.month;


-- ═════════════════════════════════════════════════════════════════════════
-- QUERY 4: Cost per production unit (efficiency KPI)
-- Business question: Which plant has the highest operational cost per unit?
-- ═════════════════════════════════════════════════════════════════════════
SELECT
    p.plant_name,
    ROUND(SUM(c.total_cost_inr), 0)                        AS total_cost_inr,
    ROUND(SUM(pr.production_units), 0)                     AS total_units,
    ROUND(SUM(c.total_cost_inr) / SUM(pr.production_units), 2) AS cost_per_unit,
    RANK() OVER (ORDER BY SUM(c.total_cost_inr) / SUM(pr.production_units) DESC)
                                                            AS efficiency_rank
FROM fact_cost c
JOIN fact_production pr USING(date, plant_id)
JOIN dim_plant p USING(plant_id)
WHERE pr.production_units > 0
GROUP BY p.plant_id, p.plant_name
ORDER BY cost_per_unit DESC;


-- ═════════════════════════════════════════════════════════════════════════
-- QUERY 5: Water quality violations by plant
-- Business question: Which plants have the most quality incidents?
-- ═════════════════════════════════════════════════════════════════════════
SELECT
    p.plant_name,
    COUNT(*)                                                AS total_readings,
    SUM(CASE WHEN q.quality_status = 'Critical' THEN 1 ELSE 0 END) AS critical_count,
    SUM(CASE WHEN q.quality_status = 'Warning'  THEN 1 ELSE 0 END) AS warning_count,
    SUM(CASE WHEN q.quality_status = 'Normal'   THEN 1 ELSE 0 END) AS normal_count,
    ROUND(
        (SUM(CASE WHEN q.quality_status IN ('Critical','Warning') THEN 1 ELSE 0 END) /
         COUNT(*)) * 100, 1
    )                                                       AS violation_pct
FROM fact_water_quality q
JOIN dim_plant p USING(plant_id)
GROUP BY p.plant_id, p.plant_name
ORDER BY critical_count DESC, warning_count DESC;


-- ═════════════════════════════════════════════════════════════════════════
-- QUERY 6: Energy efficiency per plant
-- Business question: Which plant uses the most energy per unit produced?
-- ═════════════════════════════════════════════════════════════════════════
SELECT
    p.plant_name,
    ROUND(SUM(e.energy_kwh), 0)                            AS total_kwh,
    ROUND(SUM(pr.production_units), 0)                     AS total_units,
    ROUND(SUM(e.energy_kwh) / SUM(pr.production_units), 4) AS kwh_per_unit,
    ROUND(SUM(e.energy_kwh) * 7.2, 0)                     AS energy_cost_inr
FROM fact_energy e
JOIN fact_production pr USING(date, plant_id)
JOIN dim_plant p USING(plant_id)
WHERE pr.production_units > 0
GROUP BY p.plant_id, p.plant_name
ORDER BY kwh_per_unit DESC;


-- ═════════════════════════════════════════════════════════════════════════
-- QUERY 7: Quarterly cost trend
-- Business question: Is the total operational cost increasing?
-- ═════════════════════════════════════════════════════════════════════════
SELECT
    d.quarter,
    ROUND(SUM(c.water_cost_inr), 0)     AS water_cost,
    ROUND(SUM(c.energy_cost_inr), 0)    AS energy_cost,
    ROUND(SUM(c.treatment_cost_inr), 0) AS treatment_cost,
    ROUND(SUM(c.total_cost_inr), 0)     AS total_cost,
    LAG(ROUND(SUM(c.total_cost_inr), 0)) OVER (ORDER BY d.quarter) AS prev_qtr_cost,
    ROUND(
        (SUM(c.total_cost_inr) -
         LAG(SUM(c.total_cost_inr)) OVER (ORDER BY d.quarter)) /
         LAG(SUM(c.total_cost_inr)) OVER (ORDER BY d.quarter) * 100,
    1)                                   AS qoq_change_pct
FROM fact_cost c
JOIN dim_date d ON c.date = d.date_key
GROUP BY d.quarter
ORDER BY d.quarter;


-- ═════════════════════════════════════════════════════════════════════════
-- QUERY 8: Plants with ABOVE-AVERAGE water consumption (opportunity list)
-- Business question: Where are the biggest water savings opportunities?
-- ═════════════════════════════════════════════════════════════════════════
WITH avg_consumption AS (
    SELECT AVG(water_consumption_liters) AS overall_avg
    FROM fact_water_usage
),
plant_avg AS (
    SELECT
        plant_id,
        AVG(water_consumption_liters) AS plant_avg_daily
    FROM fact_water_usage
    GROUP BY plant_id
)
SELECT
    p.plant_name,
    ROUND(pa.plant_avg_daily, 0)     AS avg_daily_liters,
    ROUND(ac.overall_avg, 0)          AS fleet_avg_liters,
    ROUND(pa.plant_avg_daily - ac.overall_avg, 0) AS excess_liters_per_day,
    ROUND((pa.plant_avg_daily - ac.overall_avg) * 365 / 1000, 0) AS annual_excess_kl,
    ROUND((pa.plant_avg_daily - ac.overall_avg) * 365 / 1000 * 18.5, 0)
                                      AS potential_savings_inr
FROM plant_avg pa
JOIN dim_plant p USING(plant_id)
CROSS JOIN avg_consumption ac
WHERE pa.plant_avg_daily > ac.overall_avg
ORDER BY excess_liters_per_day DESC;


-- ═════════════════════════════════════════════════════════════════════════
-- QUERY 9: Monthly pH trend (water quality over time)
-- Business question: Is water quality deteriorating in monsoon months?
-- ═════════════════════════════════════════════════════════════════════════
SELECT
    d.month_name,
    d.month,
    ROUND(AVG(q.ph), 2)              AS avg_ph,
    ROUND(AVG(q.turbidity_ntu), 2)   AS avg_turbidity,
    ROUND(AVG(q.tds_ppm), 1)         AS avg_tds,
    SUM(CASE WHEN q.quality_status = 'Critical' THEN 1 ELSE 0 END) AS critical_days
FROM fact_water_quality q
JOIN dim_date d ON q.date = d.date_key
GROUP BY d.month, d.month_name
ORDER BY d.month;


-- ═════════════════════════════════════════════════════════════════════════
-- QUERY 10: Plant efficiency scorecard (composite view)
-- Business question: Which plant is the best/worst overall performer?
-- ═════════════════════════════════════════════════════════════════════════
SELECT
    p.plant_name,
    p.location,
    p.plant_type,
    ROUND(SUM(w.water_consumption_liters) / 1000000, 2) AS water_ML,
    ROUND(AVG(w.recycling_percentage), 1)                AS avg_recycling_pct,
    ROUND(SUM(e.energy_kwh) / SUM(pr.production_units), 4) AS kwh_per_unit,
    ROUND(SUM(c.total_cost_inr) / SUM(pr.production_units), 2) AS cost_per_unit,
    SUM(CASE WHEN q.quality_status = 'Critical' THEN 1 ELSE 0 END) AS critical_incidents,
    SUM(pr.is_downtime)                                   AS downtime_days
FROM dim_plant p
JOIN fact_water_usage  w  USING(plant_id)
JOIN fact_energy        e  USING(plant_id)
JOIN fact_production    pr ON pr.plant_id = p.plant_id AND pr.date = e.date
JOIN fact_cost          c  ON c.plant_id  = p.plant_id AND c.date  = w.date
JOIN fact_water_quality q  ON q.plant_id  = p.plant_id AND q.date  = w.date
WHERE pr.production_units > 0
GROUP BY p.plant_id, p.plant_name, p.location, p.plant_type
ORDER BY cost_per_unit DESC;


-- ═════════════════════════════════════════════════════════════════════════
-- QUERY 11: Downtime impact on water & energy waste
-- Business question: How much resource is wasted during downtime?
-- ═════════════════════════════════════════════════════════════════════════
SELECT
    p.plant_name,
    SUM(pr.is_downtime)                    AS downtime_days,
    ROUND(SUM(CASE WHEN pr.is_downtime = 1
               THEN w.water_consumption_liters ELSE 0 END) / 1000, 0)
                                            AS water_wasted_kl,
    ROUND(SUM(CASE WHEN pr.is_downtime = 1
               THEN e.energy_kwh ELSE 0 END), 0)
                                            AS energy_wasted_kwh,
    ROUND(SUM(CASE WHEN pr.is_downtime = 1
               THEN c.total_cost_inr ELSE 0 END), 0)
                                            AS cost_during_downtime_inr
FROM fact_production pr
JOIN fact_water_usage  w  USING(date, plant_id)
JOIN fact_energy        e  USING(date, plant_id)
JOIN fact_cost          c  USING(date, plant_id)
JOIN dim_plant          p  USING(plant_id)
GROUP BY p.plant_id, p.plant_name
ORDER BY downtime_days DESC;


-- ═════════════════════════════════════════════════════════════════════════
-- QUERY 12: Water per production unit trend (efficiency over time)
-- Business question: Is operational efficiency improving?
-- ═════════════════════════════════════════════════════════════════════════
SELECT
    d.month_name,
    d.month,
    ROUND(SUM(w.water_consumption_liters) / SUM(pr.production_units), 2) AS liters_per_unit,
    ROUND(SUM(e.energy_kwh) / SUM(pr.production_units), 4)               AS kwh_per_unit,
    ROUND(SUM(c.total_cost_inr) / SUM(pr.production_units), 2)           AS cost_per_unit
FROM fact_water_usage w
JOIN fact_production   pr USING(date, plant_id)
JOIN fact_energy        e  USING(date, plant_id)
JOIN fact_cost          c  USING(date, plant_id)
JOIN dim_date           d  ON w.date = d.date_key
WHERE pr.production_units > 0
GROUP BY d.month, d.month_name
ORDER BY d.month;
