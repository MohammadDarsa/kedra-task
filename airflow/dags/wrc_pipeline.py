from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator
import pendulum
from datetime import timedelta

default_args = {
    'owner': 'darsa',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

with DAG(
    'wrc_pipeline',
    default_args=default_args,
    description='WRC Scraper and Transformer Pipeline',
    schedule=None,
    start_date=pendulum.today('UTC').add(days=-1),
    tags=['wrc', 'pipeline'],
    params={
        'start_date': '01/10/2025',
        'end_date': '01/12/2025',
        'query': 'Minimum'
    }
) as dag:

    params = "{{ params }}"
    
    run_scraper = BashOperator(
        task_id='run_scraper',
        bash_command="""
        cd /opt/airflow/scarper && \
        python -m src.main \
        --from_date '{{ params.start_date }}' \
        --to_date '{{ params.end_date }}' \
        --q '{{ params.query }}'
        """
    )

    run_transformer = BashOperator(
        task_id='run_transformer',
        bash_command="""
        cd /opt/airflow/transformer && \
        python -m src.main \
        --start_date '{{ params.start_date }}' \
        --end_date '{{ params.end_date }}'
        """
    )

    run_scraper >> run_transformer
