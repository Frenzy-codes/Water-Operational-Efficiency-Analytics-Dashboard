# SQL Analytical Query Results

> Database: `ecolab_analytics` | Execution Date: 2026-10-07

This document contains the live execution results for all 12 analytical business intelligence queries.

## QUERY 1: Total water consumption by plant (ranking)
> **Business question: Which plant consumes the most water?**

```sql
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
```

### Results:
| plant_name        | location   | plant_type    |   total_water_ML |   avg_daily_liters |   consumption_rank |
|:------------------|:-----------|:--------------|-----------------:|-------------------:|-------------------:|
| Aurangabad East   | Aurangabad | Treatment     |            25.04 |              68593 |                  1 |
| Nagpur Industrial | Nagpur     | Industrial    |            19.69 |              53936 |                  2 |
| Nashik North      | Nashik     | Treatment     |            19.65 |              53846 |                  3 |
| Mumbai West       | Mumbai     | Manufacturing |            19.62 |              53760 |                  4 |
| Pune Central      | Pune       | Treatment     |            19.62 |              53746 |                  5 |
| Solapur South     | Solapur    | Manufacturing |            19.61 |              53718 |                  6 |
| Kolhapur West     | Kolhapur   | Treatment     |            19.6  |              53708 |                  7 |
| Amravati Central  | Amravati   | Industrial    |            19.6  |              53692 |                  8 |

---

## QUERY 2: Recycling performance by plant
> **Business question: How effectively is each plant recycling water?**

```sql
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
```

### Results:
| plant_name        |   total_recycled_ML |   total_consumed_ML |   recycling_pct |
|:------------------|--------------------:|--------------------:|----------------:|
| Aurangabad East   |                8.26 |               25.04 |            33   |
| Nagpur Industrial |                6.47 |               19.69 |            32.9 |
| Nashik North      |                6.41 |               19.65 |            32.6 |
| Pune Central      |                6.38 |               19.62 |            32.5 |
| Amravati Central  |                6.28 |               19.6  |            32.1 |
| Kolhapur West     |                6.26 |               19.6  |            32   |
| Mumbai West       |                6.25 |               19.62 |            31.9 |
| Solapur South     |                6.23 |               19.61 |            31.8 |

---

## QUERY 3: Monthly water consumption trend (seasonality analysis)
> **Business question: Are there seasonal patterns in water usage?**

```sql
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
```

### Results:
| month_name   |   month |   total_water_ML |   avg_daily_liters |   monthly_recycling_pct |
|:-------------|--------:|-----------------:|-------------------:|------------------------:|
| January      |       1 |            12.07 |              48649 |                    32.9 |
| February     |       2 |            11.16 |              49807 |                    32.2 |
| March        |       3 |            13.51 |              54484 |                    32.6 |
| April        |       4 |            14.4  |              59979 |                    33   |
| May          |       5 |            16.94 |              68323 |                    31.6 |
| June         |       6 |            16.07 |              66972 |                    32   |
| July         |       7 |            14.84 |              59824 |                    32.8 |
| August       |       8 |            14.13 |              56964 |                    32.4 |
| September    |       9 |            13    |              54149 |                    31.5 |
| October      |      10 |            12.64 |              50967 |                    32.2 |
| November     |      11 |            11.94 |              49767 |                    32.1 |
| December     |      12 |            11.74 |              47320 |                    33.2 |

---

## QUERY 4: Cost per production unit (efficiency KPI)
> **Business question: Which plant has the highest operational cost per unit?**

```sql
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
```

### Results:
| plant_name        |   total_cost_inr |   total_units |   cost_per_unit |   efficiency_rank |
|:------------------|-----------------:|--------------:|----------------:|------------------:|
| Solapur South     |      5.49966e+06 |        253904 |           21.66 |                 1 |
| Nagpur Industrial |      6.59418e+06 |        320745 |           20.56 |                 2 |
| Aurangabad East   |      5.06651e+06 |        249530 |           20.3  |                 3 |
| Kolhapur West     |      4.5069e+06  |        248101 |           18.17 |                 4 |
| Pune Central      |      4.55552e+06 |        251539 |           18.11 |                 5 |
| Amravati Central  |      4.47823e+06 |        247924 |           18.06 |                 6 |
| Nashik North      |      4.52768e+06 |        251508 |           18    |                 7 |
| Mumbai West       |      5.44369e+06 |        313927 |           17.34 |                 8 |

---

## QUERY 5: Water quality violations by plant
> **Business question: Which plants have the most quality incidents?**

```sql
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
```

### Results:
| plant_name        |   total_readings |   critical_count |   warning_count |   normal_count |   violation_pct |
|:------------------|-----------------:|-----------------:|----------------:|---------------:|----------------:|
| Aurangabad East   |              365 |              346 |              19 |              0 |           100   |
| Amravati Central  |              365 |               19 |              60 |            286 |            21.6 |
| Pune Central      |              365 |               16 |              53 |            296 |            18.9 |
| Nagpur Industrial |              365 |               16 |              52 |            297 |            18.6 |
| Nashik North      |              365 |               16 |              49 |            300 |            17.8 |
| Solapur South     |              365 |               11 |              54 |            300 |            17.8 |
| Kolhapur West     |              365 |                9 |              62 |            294 |            19.5 |
| Mumbai West       |              365 |                9 |              60 |            296 |            18.9 |

---

## QUERY 6: Energy efficiency per plant
> **Business question: Which plant uses the most energy per unit produced?**

```sql
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
```

### Results:
| plant_name        |   total_kwh |   total_units |   kwh_per_unit |   energy_cost_inr |
|:------------------|------------:|--------------:|---------------:|------------------:|
| Solapur South     |      624480 |        254373 |         2.455  |       4.49626e+06 |
| Nagpur Industrial |      775608 |        322853 |         2.4024 |       5.58438e+06 |
| Mumbai West       |      622276 |        317781 |         1.9582 |       4.48039e+06 |
| Kolhapur West     |      489943 |        251147 |         1.9508 |       3.52759e+06 |
| Pune Central      |      490970 |        252162 |         1.947  |       3.53498e+06 |
| Amravati Central  |      487619 |        250713 |         1.9449 |       3.51086e+06 |
| Nashik North      |      492118 |        253947 |         1.9379 |       3.54325e+06 |
| Aurangabad East   |      487755 |        252371 |         1.9327 |       3.51184e+06 |

---

## QUERY 7: Quarterly cost trend
> **Business question: Is the total operational cost increasing?**

```sql
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
```

### Results:
|   quarter |   water_cost |   energy_cost |   treatment_cost |   total_cost |   prev_qtr_cost |   qoq_change_pct |
|----------:|-------------:|--------------:|-----------------:|-------------:|----------------:|-----------------:|
|         1 |       673404 |   7.38096e+06 |      1.34206e+06 |  9.39643e+06 |   nan           |            nan   |
|         2 |       869469 |   9.50274e+06 |      1.73655e+06 |  1.21088e+07 |     9.39643e+06 |             28.9 |
|         3 |       770016 |   8.43759e+06 |      1.53505e+06 |  1.07427e+07 |     1.21088e+07 |            -11.3 |
|         4 |       665196 |   7.32816e+06 |      1.32867e+06 |  9.32203e+06 |     1.07427e+07 |            -13.2 |

---

## QUERY 8: Plants with ABOVE-AVERAGE water consumption (opportunity list)
> **Business question: Where are the biggest water savings opportunities?**

```sql
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
```

### Results:
| plant_name      |   avg_daily_liters |   fleet_avg_liters |   excess_liters_per_day |   annual_excess_kl |   potential_savings_inr |
|:----------------|-------------------:|-------------------:|------------------------:|-------------------:|------------------------:|
| Aurangabad East |              68593 |              55625 |                   12968 |               4733 |                   87565 |

---

## QUERY 9: Monthly pH trend (water quality over time)
> **Business question: Is water quality deteriorating in monsoon months?**

```sql
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
```

### Results:
| month_name   |   month |   avg_ph |   avg_turbidity |   avg_tds |   critical_days |
|:-------------|--------:|---------:|----------------:|----------:|----------------:|
| January      |       1 |     7.14 |            3.74 |     392.5 |              33 |
| February     |       2 |     7.18 |            3.85 |     400.7 |              37 |
| March        |       3 |     7.16 |            3.85 |     392.8 |              36 |
| April        |       4 |     7.07 |            3.93 |     414.3 |              38 |
| May          |       5 |     7.11 |            3.86 |     403.5 |              39 |
| June         |       6 |     7.1  |            3.89 |     407.7 |              35 |
| July         |       7 |     6.63 |            6.13 |     488.2 |              41 |
| August       |       8 |     6.62 |            5.98 |     474.2 |              36 |
| September    |       9 |     6.68 |            5.97 |     486.2 |              37 |
| October      |      10 |     7.12 |            3.88 |     410.9 |              35 |
| November     |      11 |     7.1  |            3.95 |     421.5 |              41 |
| December     |      12 |     7.16 |            3.94 |     391.1 |              34 |

---

## QUERY 10: Plant efficiency scorecard (composite view)
> **Business question: Which plant is the best/worst overall performer?**

```sql
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
```

### Results:
| plant_name        | location   | plant_type    |   water_ML |   avg_recycling_pct |   kwh_per_unit |   cost_per_unit |   critical_incidents |   downtime_days |
|:------------------|:-----------|:--------------|-----------:|--------------------:|---------------:|----------------:|---------------------:|----------------:|
| Solapur South     | Solapur    | Manufacturing |    6941.3  |                31.8 |         2.455  |           21.67 |                 3905 |               0 |
| Nagpur Industrial | Nagpur     | Industrial    |    7074    |                32.9 |         2.4024 |           20.57 |                 5776 |               0 |
| Aurangabad East   | Aurangabad | Treatment     |    8836.71 |                33   |         1.9327 |           20.29 |               122094 |               0 |
| Kolhapur West     | Kolhapur   | Treatment     |    6897.32 |                31.9 |         1.9508 |           18.15 |                 3204 |               0 |
| Pune Central      | Pune       | Treatment     |    7023.19 |                32.6 |         1.947  |           18.11 |                 5744 |               0 |
| Amravati Central  | Amravati   | Industrial    |    6898.68 |                32.1 |         1.9449 |           18.07 |                 6764 |               0 |
| Nashik North      | Nashik     | Treatment     |    6938.03 |                32.5 |         1.9379 |           17.96 |                 5696 |               0 |
| Mumbai West       | Mumbai     | Manufacturing |    6849.91 |                31.9 |         1.9582 |           17.31 |                 3186 |               0 |

---

## QUERY 11: Downtime impact on water & energy waste
> **Business question: How much resource is wasted during downtime?**

```sql
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
```

### Results:
| plant_name        |   downtime_days |   water_wasted_kl |   energy_wasted_kwh |   cost_during_downtime_inr |
|:------------------|----------------:|------------------:|--------------------:|---------------------------:|
| Mumbai West       |              10 |               536 |               16972 |                     151102 |
| Solapur South     |              10 |               544 |               17097 |                     151446 |
| Nashik North      |               9 |               469 |               11892 |                     110929 |
| Kolhapur West     |               9 |               474 |               12257 |                     114252 |
| Amravati Central  |               9 |               495 |               12320 |                     114966 |
| Aurangabad East   |               7 |               469 |                9190 |                      96887 |
| Pune Central      |               6 |               341 |                8143 |                      75723 |
| Nagpur Industrial |               4 |               253 |                9523 |                      82196 |

---

## QUERY 12: Water per production unit trend (efficiency over time)
> **Business question: Is operational efficiency improving?**

```sql
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
```

### Results:
| month_name   |   month |   liters_per_unit |   kwh_per_unit |   cost_per_unit |
|:-------------|--------:|------------------:|---------------:|----------------:|
| January      |       1 |             63.76 |         1.787  |           16.41 |
| February     |       2 |             65.61 |         1.8793 |           17.15 |
| March        |       3 |             73.73 |         2.0649 |           18.95 |
| April        |       4 |             79.43 |         2.2236 |           20.4  |
| May          |       5 |             90.61 |         2.5384 |           23.32 |
| June         |       6 |             88.82 |         2.5019 |           22.9  |
| July         |       7 |             78.19 |         2.1988 |           20.17 |
| August       |       8 |             76.35 |         2.1664 |           19.84 |
| September    |       9 |             72.56 |         2.0352 |           18.67 |
| October      |      10 |             66.79 |         1.8973 |           17.36 |
| November     |      11 |             65.86 |         1.874  |           17.14 |
| December     |      12 |             62.18 |         1.7387 |           15.97 |

---
