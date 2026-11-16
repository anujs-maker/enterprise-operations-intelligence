# Data model and grain

`requests.csv` is the fact table at one row per service request. `customers.csv` and `employees.csv` are dimensions; `team_id`, `city` and `service_id` provide organisational and service slicing. `quality_incidents.csv` is a child fact keyed by `request_id`.

Open requests intentionally have blank `closed_at` and `turnaround_hours`, an as-of `open_age_hours`, zero recorded cost and an estimated remaining cost. Closed requests have completion timestamps, turnaround and recorded cost. This prevents future-completion leakage.
