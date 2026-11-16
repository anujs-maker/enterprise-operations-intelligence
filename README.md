# Enterprise Operations & Business Performance Intelligence

An end-to-end analytics portfolio project for a simulated India-wide business-services organisation. It demonstrates operational SQL, Python data validation, KPI reconciliation, scenario modelling, executive reporting and technology-business analysis.

## Scope and disclosure

All data is deterministic synthetic data generated with seed `42`; no corporate or client data is represented. Findings are observations in the simulation, while opportunity values are modelled scenarios, not realised savings.

## Run it

```bash
python3 scripts/run_pipeline.py
python3 -m unittest discover -s tests -v
open dashboards/executive_dashboard.html
```

The standard-library implementation runs without external services. Optional pandas/DuckDB upgrades are documented in `requirements.txt` and the SQL is also runnable in SQLite/DuckDB with minor date-function adjustments.

## Outputs

- `data/processed/requests.csv` and linked dimension tables (500,000 generated requests)
- `reports/executive_summary/executive_memo.md`
- `reports/findings/findings.md`
- `data/processed/reconciliation_report.json` (executed SQL/Python KPI reconciliation)
- `dashboards/executive_dashboard.html` (interactive HTML dashboard, not a PBIX)
- `powerbi/README.md` and `powerbi/dax_measures.md` for native Power BI reconstruction
- BRD, stakeholder map, requirements, KPI dictionary, process/data-flow diagrams, UAT and traceability under `docs/`
- `INTERVIEW_PLAYBOOK.md` is intentionally private and excluded from GitHub

## Architecture

Synthetic generator → validation/KPI pipeline → SQLite analytical model → SQL analysis → JSON reporting tables → browser dashboard. A Power BI-ready star-schema export and DAX definitions are included, but a genuine PBIX cannot be authored in this environment.

The pipeline fails when SQL and independent Python KPI values disagree beyond documented tolerances. The financial scenario is monthly and scoped to Gurugram Payments Operations rather than applying an organisation-wide percentage; assumptions are documented in `docs/scenario_assumptions.md`.

## Reproducibility

`scripts/run_pipeline.py` recreates the dataset and reports from scratch. No credentials, virtual environments or generated large files are committed.

## License

MIT. Synthetic data is original to this project.
