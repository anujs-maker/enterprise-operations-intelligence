```DAX
Total Requests = COUNTROWS(Requests)
Closed Requests = CALCULATE([Total Requests], Requests[status] = "Closed")
SLA Compliance % = DIVIDE(CALCULATE([Closed Requests], Requests[turnaround_hours] <= Requests[sla_hours]), [Closed Requests])
Average TAT Hours = AVERAGE(Requests[turnaround_hours])
Operating Cost = SUM(Requests[cost_inr])
Backlog = CALCULATE([Total Requests], Requests[status] = "Open")
```
