import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # mongo
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://root:mongopassword@localhost:27017/')
    MONGO_DB_NAME = os.getenv('MONGO_DATABASE', 'wrc_db')
    SOURCE_COLLECTION = 'wrc_decisions'
    TARGET_COLLECTION = 'wrc_decisions_processed'

    # minio
    MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT', 'localhost:9000')
    MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
    MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY', 'minioadmin')
    SOURCE_BUCKET = os.getenv('MINIO_BUCKET', 'wrc-decisions')
    TARGET_BUCKET = 'wrc-processed'
