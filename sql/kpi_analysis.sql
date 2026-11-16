-- Business question: which cities combine volume, cost and SLA risk?
SELECT city, COUNT(*) AS requests,
       ROUND(100.0*AVG(CASE WHEN turnaround_hours <= sla_hours THEN 1 ELSE 0 END),2) AS sla_compliance_pct,
       ROUND(AVG(turnaround_hours),2) AS avg_turnaround_hours,
       ROUND(SUM(cost_inr),2) AS cost_inr
FROM requests WHERE status='Closed' GROUP BY city ORDER BY sla_compliance_pct;

-- Root-cause segmentation by complexity
SELECT complexity, COUNT(*) AS requests, ROUND(AVG(turnaround_hours),2) AS avg_hours,
       ROUND(100.0*AVG(CASE WHEN turnaround_hours > sla_hours THEN 1 ELSE 0 END),2) AS breach_pct
FROM requests GROUP BY complexity ORDER BY breach_pct DESC;

-- Backlog ageing and overdue exposure as of the configured report date
SELECT city, COUNT(*) AS backlog,
       SUM(CASE WHEN open_age_hours > sla_hours THEN 1 ELSE 0 END) AS overdue,
       ROUND(AVG(open_age_hours),2) AS avg_age_hours,
       ROUND(SUM(estimated_remaining_cost_inr),2) AS estimated_remaining_cost
FROM requests WHERE status='Open' GROUP BY city ORDER BY overdue DESC;

-- Window-function period-over-period view
WITH monthly AS (
  SELECT substr(opened_at,1,7) AS month, city, COUNT(*) AS volume,
         AVG(CASE WHEN status='Closed' AND turnaround_hours <= sla_hours THEN 1.0 ELSE 0 END) AS sla_rate
  FROM requests GROUP BY substr(opened_at,1,7), city
), ranked AS (
  SELECT *, LAG(sla_rate) OVER (PARTITION BY city ORDER BY month) AS prior_sla_rate
  FROM monthly
)
SELECT month, city, volume, ROUND(100*sla_rate,2) AS sla_pct,
       ROUND(100*(sla_rate-prior_sla_rate),2) AS change_vs_prior_pp
FROM ranked ORDER BY month, city;

-- Productivity and quality signal by team
SELECT team_id, COUNT(*) AS handled, ROUND(AVG(turnaround_hours),2) AS avg_tat,
       ROUND(AVG(quality_score),2) AS avg_quality,
       ROUND(SUM(cost_inr)/COUNT(*),2) AS cost_per_completed_case
FROM requests WHERE status='Closed' GROUP BY team_id ORDER BY cost_per_completed_case DESC;
