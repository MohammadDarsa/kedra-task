import argparse
import logging
import os
from datetime import datetime
from src.services.mongo_service import MongoService
from src.services.minio_service import MinioService
from src.utils.utils import process_html_content, calculate_hash

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Transformer:
    def __init__(self):
        self.mongo_service = MongoService()
        self.minio_service = MinioService()

    def run(self, start_date_str, end_date_str):
        try:
            start_date = datetime.strptime(start_date_str, "%d/%m/%Y")
            end_date = datetime.strptime(end_date_str, "%d/%m/%Y")
        except ValueError as e:
            logger.error(f"invalid date format. use dd/mm/yyyy. error: {e}")
            return

        logger.info(f"processing records from {start_date_str} to {end_date_str}")
        
        docs = self.mongo_service.get_records_by_date_range(start_date, end_date)
        processed_count = 0
        
        for doc in docs:
            ref_number = doc.get('ref_number')
            if ref_number:
                # after testing turns out ref number has leading/trailing spaces in some cases
                ref_number = ref_number.strip()
            
            file_path = doc.get('file_path')
            
            if not ref_number or not file_path:
                logger.warning(f"skipping doc with missing ref_number or file_path: {doc.get('_id')}")
                continue

            _, ext = os.path.splitext(file_path)
            logger.info(f"processing case {ref_number}")
            source_files = self.minio_service.list_files(file_path)
            
            if not source_files:
                logger.warning(f"no files found in {file_path}")
                continue

            partition_date = doc.get('partition_date', 'unknown').replace('/', '-')
            published_date = doc.get('published_date', 'unknown').replace('/', '-')
            
            target_prefix = f"files/{partition_date}/{published_date}/{ref_number}/"
            
            processed_attachments = []
            main_file_hash = None
            
            for s3_file_path in source_files:
                content, obj_name = self.minio_service.get_file_content(s3_file_path)
                if content is None:
                    continue
                
                fname = os.path.basename(obj_name)
                _, fext = os.path.splitext(fname)
                is_html = fext.lower() in ['.html', '.htm']
                
                new_content = content
                if is_html:
                    new_content = process_html_content(content)
                
                new_filename = f"{target_prefix}{fname}"
                
                try:
                    uploaded_path = self.minio_service.upload_file(
                        new_filename, 
                        new_content, 
                        content_type='text/html' if is_html else 'application/octet-stream'
                    )
                    
                    if fname.startswith(ref_number):
                        main_file_hash = calculate_hash(new_content)
                    else:
                        processed_attachments.append(uploaded_path)
                        
                except Exception:
                    logger.error(f"failed to process/upload {fname}")
                    continue
            
            new_record = doc.copy()
            new_record['file_path'] = f"s3://{Settings.TARGET_BUCKET}/{target_prefix}"
            new_record['file_hash'] = main_file_hash
            new_record['additional_files'] = processed_attachments
            
            self.mongo_service.upsert_processed_record(new_record)
            
            processed_count += 1
            
        logger.info(f"transformer finished. processed {processed_count} records.")

def main():
    parser = argparse.ArgumentParser(description='wrc transformer')
    parser.add_argument('--start_date', required=True, help='start date (dd/mm/yyyy)')
    parser.add_argument('--end_date', required=True, help='end date (dd/mm/yyyy)')
    
    args = parser.parse_args()
    
    transformer = Transformer()
    transformer.run(args.start_date, args.end_date)

if __name__ == "__main__":
    main()
