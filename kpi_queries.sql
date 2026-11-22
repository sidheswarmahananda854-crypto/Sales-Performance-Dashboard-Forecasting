-- SYNTHETIC retail sales: KPI queries (SQLite). Revenue = qty * unit_price * (1 - discount); profit = revenue - qty*unit_cost.
CREATE VIEW IF NOT EXISTS v_sales AS
SELECT oi.item_id, o.order_id, o.order_date, substr(o.order_date,1,7) AS ym, substr(o.order_date,1,4) AS yr,
       o.customer_id, r.region_name, p.product_name, p.category, oi.quantity, oi.discount,
       oi.quantity*p.unit_price*(1-oi.discount) AS revenue,
       oi.quantity*p.unit_price*(1-oi.discount) - oi.quantity*p.unit_cost AS profit
FROM order_items oi JOIN orders o USING(order_id) JOIN products p USING(product_id) JOIN regions r USING(region_id);

-- Q01 Headline KPIs
SELECT COUNT(DISTINCT order_id) orders, COUNT(*) line_items, ROUND(SUM(revenue)) revenue, ROUND(SUM(profit)) profit,
       ROUND(100.0*SUM(profit)/SUM(revenue),1) margin_pct, ROUND(SUM(revenue)/COUNT(DISTINCT order_id),2) aov FROM v_sales;

-- Q02 Yearly revenue and YoY growth (CTE + LAG)
WITH y AS (SELECT yr, SUM(revenue) rev, SUM(profit) prof FROM v_sales GROUP BY yr)
SELECT yr, ROUND(rev) revenue, ROUND(prof) profit,
       ROUND(100.0*(rev-LAG(rev) OVER (ORDER BY yr))/LAG(rev) OVER (ORDER BY yr),1) yoy_growth_pct FROM y;

-- Q03 Monthly revenue, MoM growth, 3-month moving average
WITH m AS (SELECT ym, SUM(revenue) rev FROM v_sales GROUP BY ym)
SELECT ym, ROUND(rev) revenue,
       ROUND(100.0*(rev-LAG(rev) OVER (ORDER BY ym))/LAG(rev) OVER (ORDER BY ym),1) mom_pct,
       ROUND(AVG(rev) OVER (ORDER BY ym ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)) ma3 FROM m ORDER BY ym;

-- Q04 Regional performance with revenue share and rank
WITH r AS (SELECT region_name, SUM(revenue) rev, SUM(profit) prof, COUNT(DISTINCT order_id) orders FROM v_sales GROUP BY region_name)
SELECT region_name, ROUND(rev) revenue, ROUND(prof) profit, ROUND(100.0*prof/rev,1) margin_pct, orders,
       ROUND(100.0*rev/SUM(rev) OVER (),1) share_pct, RANK() OVER (ORDER BY rev DESC) rev_rank FROM r;

-- Q05 Regional YoY growth: flag underperforming regions
WITH ry AS (SELECT region_name, yr, SUM(revenue) rev FROM v_sales GROUP BY region_name, yr)
SELECT region_name, yr, ROUND(rev) revenue,
       ROUND(100.0*(rev-LAG(rev) OVER (PARTITION BY region_name ORDER BY yr))/LAG(rev) OVER (PARTITION BY region_name ORDER BY yr),1) yoy_pct
FROM ry ORDER BY region_name, yr;

-- Q06 Category profitability
SELECT category, ROUND(SUM(revenue)) revenue, ROUND(SUM(profit)) profit, ROUND(100.0*SUM(profit)/SUM(revenue),1) margin_pct,
       ROUND(100.0*SUM(revenue)/(SELECT SUM(revenue) FROM v_sales),1) share_pct FROM v_sales GROUP BY category ORDER BY revenue DESC;

-- Q07 Top 3 products per category (ROW_NUMBER)
WITH p AS (SELECT category, product_name, SUM(revenue) rev, SUM(profit) prof FROM v_sales GROUP BY category, product_name),
     rk AS (SELECT *, ROW_NUMBER() OVER (PARTITION BY category ORDER BY rev DESC) rn FROM p)
SELECT category, product_name, ROUND(rev) revenue, ROUND(prof) profit, rn FROM rk WHERE rn<=3 ORDER BY category, rn;

-- Q08 Average order value by month
SELECT ym, ROUND(SUM(revenue)/COUNT(DISTINCT order_id),2) aov, COUNT(DISTINCT order_id) orders FROM v_sales GROUP BY ym ORDER BY ym;

-- Q09 Seasonality index: avg monthly revenue vs overall monthly mean
WITH m AS (SELECT CAST(substr(ym,6,2) AS INT) mo, ym, SUM(revenue) rev FROM v_sales GROUP BY ym)
SELECT mo, ROUND(AVG(rev)) avg_rev, ROUND(AVG(rev)/(SELECT AVG(rev) FROM m),2) seasonality_idx FROM m GROUP BY mo ORDER BY mo;

-- Q10 Discount depth vs margin
SELECT discount, COUNT(*) items, ROUND(SUM(revenue)) revenue, ROUND(100.0*SUM(profit)/SUM(revenue),1) margin_pct FROM v_sales GROUP BY discount ORDER BY discount;

-- Q11 Repeat customers: share of customers with 2+ orders
WITH c AS (SELECT customer_id, COUNT(DISTINCT order_id) n FROM v_sales GROUP BY customer_id)
SELECT COUNT(*) customers, SUM(n>=2) repeat_customers, ROUND(100.0*SUM(n>=2)/COUNT(*),1) repeat_pct FROM c;

-- Q12 Region x category revenue heatmap with rank inside region
WITH rc AS (SELECT region_name, category, SUM(revenue) rev FROM v_sales GROUP BY region_name, category)
SELECT region_name, category, ROUND(rev) revenue, RANK() OVER (PARTITION BY region_name ORDER BY rev DESC) cat_rank_in_region FROM rc ORDER BY region_name, cat_rank_in_region;

-- Q13 Cumulative revenue (running total) by month within each year
WITH m AS (SELECT yr, ym, SUM(revenue) rev FROM v_sales GROUP BY yr, ym)
SELECT yr, ym, ROUND(rev) revenue, ROUND(SUM(rev) OVER (PARTITION BY yr ORDER BY ym)) ytd_revenue FROM m ORDER BY ym;
