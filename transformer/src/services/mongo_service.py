import pymongo
import logging
from src.settings import Settings

logger = logging.getLogger(__name__)

class MongoService:
    def __init__(self):
        try:
            self.client = pymongo.MongoClient(Settings.MONGO_URI)
            self.db = self.client[Settings.MONGO_DB_NAME]
            logger.info("connected to mongodb")
        except Exception as e:
            logger.error(f"failed to connect to mongodb: {e}")
            raise

    def get_records_by_date_range(self, start_date, end_date):
        pipeline = [
            {
                "$addFields": {
                    "date_obj": {
                        "$dateFromString": {
                            "dateString": "$published_date",
                            "format": "%d/%m/%Y",
                            "onError": None,
                            "onNull": None
                        }
                    }
                }
            },
            {
                "$match": {
                    "date_obj": {
                        "$gte": start_date,
                        "$lte": end_date
                    },
                    "file_path": {"$exists": True, "$ne": None}
                }
            }
        ]
        return self.db[Settings.SOURCE_COLLECTION].aggregate(pipeline)

    def upsert_processed_record(self, record):
        try:
            record_to_save = record.copy()
            record_to_save.pop('date_obj', None)
            record_to_save.pop('_id', None)
            from datetime import datetime
            record_to_save['processed_at'] = datetime.utcnow()
            
            self.db[Settings.TARGET_COLLECTION].update_one(
                {'ref_number': record['ref_number']},
                {'$set': record_to_save},
                upsert=True
            )
        except Exception as e:
            logger.error(f"failed to upsert record {record.get('ref_number')}: {e}")
