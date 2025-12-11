import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # mongo
    MONGO_URI = os.getenv('MONGO_URI')
    MONGO_DATABASE = os.getenv('MONGO_DATABASE')
    
    # minio
    MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT')
    MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY')
    MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY')
    MINIO_BUCKET = os.getenv('MINIO_BUCKET')

def get_settings(debug=False):
    return {
        'BOT_NAME': 'wrc_scraper',
        'ROBOTSTXT_OBEY': False,
        'USER_AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
        'COOKIES_ENABLED': True,
        'ITEM_PIPELINES': {
           'src.pipelines.minio_pipeline.MinioPipeline': 200, # lower number means higher priority
           'src.pipelines.mongo_pipeline.MongoPipeline': 300,
        },
        'MONGO_URI': Settings.MONGO_URI,
        'MONGO_DATABASE': Settings.MONGO_DATABASE,
        'MINIO_ENDPOINT': Settings.MINIO_ENDPOINT,
        'MINIO_ACCESS_KEY': Settings.MINIO_ACCESS_KEY,
        'MINIO_SECRET_KEY': Settings.MINIO_SECRET_KEY,
        'MINIO_BUCKET': Settings.MINIO_BUCKET,
        'LOG_LEVEL': 'DEBUG' if debug else 'INFO',
    }
