# UK49 ETL Pipeline (Airflow + FastAPI + Streamlit + PostgreSQL)

This repository provides a scaffold for a UK49 lottery ETL pipeline using:
- Airflow (DAGs) for orchestration
- FastAPI for an API service
- Streamlit for a lightweight dashboard
- PostgreSQL as the primary datastore

Quick start (development):

1. Copy `.env.example` to `.env` and edit values.
2. Build and start services with Docker Compose:

```bash
docker-compose up --build
```

3. FastAPI: http://localhost:8000
4. Streamlit: http://localhost:8501
5. Airflow UI: http://localhost:8080

Files created:
- [docker-compose.yml](docker-compose.yml)
- [airflow/dags/uk49_dag.py](airflow/dags/uk49_dag.py)
- [api/main.py](api/main.py)
- [app/streamlit_app.py](app/streamlit_app.py)
- [requirements.txt](requirements.txt)

Extend ETL logic in `airflow/scripts/etl_tasks.py` and data models in `api/models.py`.
