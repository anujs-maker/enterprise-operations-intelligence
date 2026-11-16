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
