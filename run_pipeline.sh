#!/bin/bash
START_DATE="01/10/2025"
END_DATE="01/12/2025"
QUERY="Minimum"

# run docker compose
docker-compose up -d
# wait for docker to stabilize
sleep 5

cd scarper
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "creating virtual environment for scraper..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
fi

echo "executing scraper with query='$QUERY' from $START_DATE to $END_DATE"
python -m src.main --q "$QUERY" --from_date "$START_DATE" --to_date "$END_DATE"

deactivate
cd ..
cd transformer

if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "creating virtual environment for transformer..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
fi

echo "executing transformer from $START_DATE to $END_DATE"
python -m src.main --start_date "$START_DATE" --end_date "$END_DATE"

deactivate
cd ..
echo "pipeline finished successfully."
