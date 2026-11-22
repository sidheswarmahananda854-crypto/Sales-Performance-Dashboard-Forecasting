# Sales Dashboard & Forecasting 

End-to-end regional sales analysis: SQL KPIs, Python time-series forecast, Excel dashboard.

**Data is synthetic.** `generate_data.py` creates a seeded, reproducible dataset (2023-2025): 1.37M orders, 2.57M order lines, 150 products, 6 categories, 5 regions, built-in seasonality, growth and one deliberately shrinking region (Central). No real company data is used.

| Step | File |
|---|---|
| Generate data into SQLite | `generate_data.py` |
| 13 KPI queries (CTEs, window functions, joins) | `sql/kpi_queries.sql`, run with `run_sql.py` |
| Forecast with validation (6-month holdout) | `notebooks/sales_forecasting.ipynb` |
| Dashboard | `excel/sales_dashboard.xlsx` |

Run: `python generate_data.py && python run_sql.py && python build_notebook.py` (notebook needs `statsmodels`).

## Results (on the synthetic data)
- Revenue $253.2M, profit margin 21.1%, AOV $185, 2025 YoY growth +8.3%.
- Holdout MAPE: Holt-Winters 1.2%, SARIMA 1.4%, seasonal naive 0.7% (benchmark).
- Central region declining about 11-12% a year; flagged as underperforming.
- 20% discounts cut margin to 8.7% vs 26.9% at no discount.
