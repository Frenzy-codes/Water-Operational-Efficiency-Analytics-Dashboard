-- ─────────────────────────────────────────────────────────────────────────
-- views.sql
-- Water & Operational Efficiency Analytics Dashboard
-- Reusable SQL Views — Power BI can connect directly to these
-- ─────────────────────────────────────────────────────────────────────────

USE ecolab_analytics;

-- ═════════════════════════════════════════════════════════════════════════
-- VIEW 1: vw_plant_summary
-- Aggregated KPIs per plant (full year summary)
-- Use in Power BI for plant comparison tables and bar charts
-- ═════════════════════════════════════════════════════════════════════════
CREATE OR REPLACE VIEW vw_plant_summary AS
SELECT
    p.plant_id,
    p.plant_name,
    p.location,
    p.plant_type,
    p.capacity_liters,

    -- Water KPIs
    ROUND(SUM(w.water_consumption_liters) / 1000000, 3)   AS total_water_ML,
    ROUND(SUM(w.recycled_water_liters)    / 1000000, 3)   AS total_recycled_ML,
    ROUND(AVG(w.recycling_percentage), 1)                  AS avg_recycling_pct,
    ROUND(AVG(w.water_consumption_liters), 0)              AS avg_daily_water_L,

    -- Energy KPIs
    ROUND(SUM(e.energy_kwh), 0)                            AS total_energy_kwh,
    ROUND(AVG(e.energy_kwh), 1)                            AS avg_daily_kwh,

    -- Production KPIs
    ROUND(SUM(pr.production_units), 0)                     AS total_production,
    SUM(pr.is_downtime)                                    AS downtime_days,

    -- Cost KPIs
    ROUND(SUM(c.total_cost_inr), 0)                        AS total_cost_inr,
    ROUND(SUM(c.water_cost_inr), 0)                        AS total_water_cost_inr,
    ROUND(SUM(c.energy_cost_inr), 0)                       AS total_energy_cost_inr,
    ROUND(SUM(c.treatment_cost_inr), 0)                    AS total_treatment_cost_inr,

    -- Efficiency KPIs
    ROUND(SUM(c.total_cost_inr) / NULLIF(SUM(pr.production_units), 0), 2) AS cost_per_unit,
    ROUND(SUM(w.water_consumption_liters) / NULLIF(SUM(pr.production_units), 0), 2) AS water_per_unit,
    ROUND(SUM(e.energy_kwh) / NULLIF(SUM(pr.production_units), 0), 4)     AS kwh_per_unit,

    -- Quality KPIs
    ROUND(AVG(q.ph), 2)                                    AS avg_ph,
    ROUND(AVG(q.turbidity_ntu), 2)                         AS avg_turbidity,
    ROUND(AVG(q.tds_ppm), 1)                               AS avg_tds,
    SUM(CASE WHEN q.quality_status = 'Critical' THEN 1 ELSE 0 END) AS critical_incidents,
    SUM(CASE WHEN q.quality_status = 'Warning'  THEN 1 ELSE 0 END) AS warning_incidents

FROM dim_plant p
JOIN fact_water_usage  w  USING(plant_id)
JOIN fact_energy        e  ON e.plant_id = p.plant_id AND e.date = w.date
JOIN fact_production    pr ON pr.plant_id = p.plant_id AND pr.date = w.date
JOIN fact_cost          c  ON c.plant_id  = p.plant_id AND c.date  = w.date
JOIN fact_water_quality q  ON q.plant_id  = p.plant_id AND q.date  = w.date
GROUP BY p.plant_id, p.plant_name, p.location, p.plant_type, p.capacity_liters;


-- ═════════════════════════════════════════════════════════════════════════
-- VIEW 2: vw_monthly_trend
-- Month-level time series across all plants
-- Use in Power BI for line charts and trend analysis
-- ═════════════════════════════════════════════════════════════════════════
CREATE OR REPLACE VIEW vw_monthly_trend AS
SELECT
    d.year,
    d.month,
    d.month_name,
    d.quarter,

    -- Water
    ROUND(SUM(w.water_consumption_liters) / 1000000, 3)  AS total_water_ML,
    ROUND(SUM(w.recycled_water_liters)    / 1000000, 3)  AS total_recycled_ML,
    ROUND(SUM(w.recycled_water_liters) /
          NULLIF(SUM(w.water_consumption_liters), 0) * 100, 1) AS recycling_pct,

    -- Energy
    ROUND(SUM(e.energy_kwh), 0)                           AS total_energy_kwh,

    -- Production
    ROUND(SUM(pr.production_units), 0)                    AS total_production,
    SUM(pr.is_downtime)                                   AS downtime_days,

    -- Costs
    ROUND(SUM(c.total_cost_inr), 0)                       AS total_cost_inr,
    ROUND(SUM(c.water_cost_inr), 0)                       AS water_cost_inr,
    ROUND(SUM(c.energy_cost_inr), 0)                      AS energy_cost_inr,
    ROUND(SUM(c.treatment_cost_inr), 0)                   AS treatment_cost_inr,

    -- Efficiency
    ROUND(SUM(c.total_cost_inr) / NULLIF(SUM(pr.production_units), 0), 2) AS cost_per_unit,
    ROUND(SUM(w.water_consumption_liters) / NULLIF(SUM(pr.production_units), 0), 2) AS water_per_unit,

    -- Quality
    ROUND(AVG(q.ph), 2)            AS avg_ph,
    ROUND(AVG(q.turbidity_ntu), 2) AS avg_turbidity,
    ROUND(AVG(q.tds_ppm), 1)       AS avg_tds,
    SUM(CASE WHEN q.quality_status IN ('Critical','Warning') THEN 1 ELSE 0 END) AS quality_violations

FROM fact_water_usage w
JOIN dim_date          d  ON w.date = d.date_key
JOIN fact_energy        e  USING(date, plant_id)
JOIN fact_production    pr USING(date, plant_id)
JOIN fact_cost          c  USING(date, plant_id)
JOIN fact_water_quality q  USING(date, plant_id)
GROUP BY d.year, d.month, d.month_name, d.quarter
ORDER BY d.year, d.month;


-- ═════════════════════════════════════════════════════════════════════════
-- VIEW 3: vw_quality_alerts
-- All Warning and Critical water quality readings
-- Use in Power BI for alert tables with conditional formatting
-- ═════════════════════════════════════════════════════════════════════════
CREATE OR REPLACE VIEW vw_quality_alerts AS
SELECT
    q.date,
    p.plant_name,
    p.location,
    q.ph,
    q.turbidity_ntu,
    q.tds_ppm,
    q.quality_status,
    d.month_name,
    d.quarter,
    -- Flag specific parameter violations
    CASE WHEN q.ph < 5.5 OR q.ph > 9.5 THEN 'Yes' ELSE 'No' END AS ph_violation,
    CASE WHEN q.turbidity_ntu > 10      THEN 'Yes' ELSE 'No' END AS turbidity_violation,
    CASE WHEN q.tds_ppm > 1000          THEN 'Yes' ELSE 'No' END AS tds_violation,
    -- Severity score (for sorting)
    CASE quality_status WHEN 'Critical' THEN 3 WHEN 'Warning' THEN 2 ELSE 1 END AS severity_score
FROM fact_water_quality q
JOIN dim_plant p USING(plant_id)
JOIN dim_date  d ON q.date = d.date_key
WHERE q.quality_status IN ('Warning', 'Critical')
ORDER BY q.date DESC, severity_score DESC;
