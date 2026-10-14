-- ─────────────────────────────────────────────────────────────────────────
-- schema.sql
-- Water & Operational Efficiency Analytics Dashboard
-- Star Schema DDL for ecolab_analytics database
-- ─────────────────────────────────────────────────────────────────────────

CREATE DATABASE IF NOT EXISTS ecolab_analytics
    DEFAULT CHARACTER SET utf8mb4;

USE ecolab_analytics;

-- ─────────────────────────────────────────────────────────────────────────
-- DIMENSION TABLES
-- ─────────────────────────────────────────────────────────────────────────

DROP TABLE IF EXISTS fact_water_usage;
DROP TABLE IF EXISTS fact_water_quality;
DROP TABLE IF EXISTS fact_energy;
DROP TABLE IF EXISTS fact_production;
DROP TABLE IF EXISTS fact_cost;
DROP TABLE IF EXISTS dim_plant;
DROP TABLE IF EXISTS dim_date;

-- dim_plant ──────────────────────────────────────────────────────────────
CREATE TABLE dim_plant (
    plant_id        VARCHAR(10)  NOT NULL,
    plant_name      VARCHAR(100) NOT NULL,
    location        VARCHAR(100) NOT NULL,
    plant_type      VARCHAR(50)  NOT NULL,
    capacity_liters FLOAT        NOT NULL,
    PRIMARY KEY (plant_id)
);

-- dim_date ───────────────────────────────────────────────────────────────
CREATE TABLE dim_date (
    date_key     DATE        NOT NULL,
    year         SMALLINT    NOT NULL,
    month        TINYINT     NOT NULL,
    month_name   VARCHAR(15) NOT NULL,
    quarter      TINYINT     NOT NULL,
    day_of_week  VARCHAR(10) NOT NULL,
    is_weekend   TINYINT     NOT NULL DEFAULT 0,
    week_of_year TINYINT     NOT NULL,
    PRIMARY KEY (date_key)
);

-- ─────────────────────────────────────────────────────────────────────────
-- FACT TABLES
-- ─────────────────────────────────────────────────────────────────────────

-- fact_water_usage ────────────────────────────────────────────────────────
CREATE TABLE fact_water_usage (
    date                      DATE        NOT NULL,
    plant_id                  VARCHAR(10) NOT NULL,
    water_consumption_liters  FLOAT       NOT NULL,
    recycled_water_liters     FLOAT       NOT NULL DEFAULT 0,
    recycling_percentage      FLOAT       NOT NULL DEFAULT 0,
    net_water_liters          FLOAT       NOT NULL DEFAULT 0,
    PRIMARY KEY (date, plant_id),
    FOREIGN KEY (plant_id) REFERENCES dim_plant(plant_id),
    FOREIGN KEY (date)     REFERENCES dim_date(date_key)
);

-- fact_water_quality ──────────────────────────────────────────────────────
CREATE TABLE fact_water_quality (
    date           DATE        NOT NULL,
    plant_id       VARCHAR(10) NOT NULL,
    ph             FLOAT       NOT NULL,
    turbidity_ntu  FLOAT       NOT NULL,
    tds_ppm        FLOAT       NOT NULL,
    quality_status VARCHAR(20) NOT NULL DEFAULT 'Normal',
    PRIMARY KEY (date, plant_id),
    FOREIGN KEY (plant_id) REFERENCES dim_plant(plant_id),
    FOREIGN KEY (date)     REFERENCES dim_date(date_key)
);

-- fact_energy ─────────────────────────────────────────────────────────────
CREATE TABLE fact_energy (
    date        DATE        NOT NULL,
    plant_id    VARCHAR(10) NOT NULL,
    energy_kwh  FLOAT       NOT NULL,
    PRIMARY KEY (date, plant_id),
    FOREIGN KEY (plant_id) REFERENCES dim_plant(plant_id),
    FOREIGN KEY (date)     REFERENCES dim_date(date_key)
);

-- fact_production ─────────────────────────────────────────────────────────
CREATE TABLE fact_production (
    date             DATE        NOT NULL,
    plant_id         VARCHAR(10) NOT NULL,
    production_units FLOAT       NOT NULL,
    is_downtime      TINYINT     NOT NULL DEFAULT 0,
    PRIMARY KEY (date, plant_id),
    FOREIGN KEY (plant_id) REFERENCES dim_plant(plant_id),
    FOREIGN KEY (date)     REFERENCES dim_date(date_key)
);

-- fact_cost ───────────────────────────────────────────────────────────────
CREATE TABLE fact_cost (
    date                  DATE        NOT NULL,
    plant_id              VARCHAR(10) NOT NULL,
    water_cost_inr        FLOAT       NOT NULL DEFAULT 0,
    energy_cost_inr       FLOAT       NOT NULL DEFAULT 0,
    treatment_cost_inr    FLOAT       NOT NULL DEFAULT 0,
    total_cost_inr        FLOAT       NOT NULL DEFAULT 0,
    cost_per_unit         FLOAT,
    cost_per_kl           FLOAT,
    PRIMARY KEY (date, plant_id),
    FOREIGN KEY (plant_id) REFERENCES dim_plant(plant_id),
    FOREIGN KEY (date)     REFERENCES dim_date(date_key)
);

-- ─────────────────────────────────────────────────────────────────────────
-- INDEXES for Power BI query performance
-- ─────────────────────────────────────────────────────────────────────────
CREATE INDEX idx_wu_plant ON fact_water_usage  (plant_id);
CREATE INDEX idx_wq_plant ON fact_water_quality(plant_id);
CREATE INDEX idx_en_plant ON fact_energy       (plant_id);
CREATE INDEX idx_pr_plant ON fact_production   (plant_id);
CREATE INDEX idx_co_plant ON fact_cost         (plant_id);
