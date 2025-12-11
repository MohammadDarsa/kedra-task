import boto3
import requests
import io
import os
import hashlib
from botocore.client import Config

class MinioPipeline:
    def __init__(self, endpoint, access_key, secret_key, bucket_name):
        self.endpoint = endpoint
        self.access_key = access_key
        self.secret_key = secret_key
        self.bucket_name = bucket_name
        self.s3_client = None

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            endpoint=crawler.settings.get('MINIO_ENDPOINT', 'http://localhost:9000'),
            access_key=crawler.settings.get('MINIO_ACCESS_KEY', 'minioadmin'),
            secret_key=crawler.settings.get('MINIO_SECRET_KEY', 'minioadmin'),
            bucket_name=crawler.settings.get('MINIO_BUCKET', 'wrc-decisions')
        )

    def open_spider(self, spider):
        self.s3_client = boto3.client('s3',
                                      endpoint_url=self.endpoint,
                                      aws_access_key_id=self.access_key,
                                      aws_secret_access_key=self.secret_key,
                                      config=Config(signature_version='s3v4'),
                                      region_name='us-east-1') 
        
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except:
            spider.logger.info(f"bucket {self.bucket_name} not found, creating...")
            try:
                # NOTE: only added this for the ease of use, in reality buckets should be managed outside of the application
                self.s3_client.create_bucket(Bucket=self.bucket_name)
            except Exception as e:
                 spider.logger.error(f"failed to create bucket: {e}")

    def process_item(self, item, spider):
        url = item.get('url')
        ref_number = item.get('ref_number')
        partition_date = item.get('partition_date', 'unknown').replace('/', '-')
        published_date = item.get('published_date', 'unknown').replace('/', '-')
        additional_files = item.get('additional_files', [])
        
        if not url:
            return item

        folder_prefix = f"files/{partition_date}/{published_date}/{ref_number}/"
        
        
        try:
            _, ext = os.path.splitext(url)
            if not ext:
                ext = '.html' # default to HTML
            
            main_filename = f"{folder_prefix}{ref_number}{ext}"
            
            try:
                self.s3_client.head_object(Bucket=self.bucket_name, Key=main_filename)
                spider.logger.info(f"file {main_filename} already exists. skipping download.")
                item['file_path'] = f"s3://{self.bucket_name}/{folder_prefix}"
                return item # skip attachment processing as well? Yes per requirement ("don't create a new record or upload a new file")
            except:
                pass

            self._download_and_upload(url, main_filename, spider, item, is_main=True)
            
            for file_url in additional_files:
                fname = os.path.basename(file_url)
                if not fname:
                    fname = f"attachment_{hashlib.md5(file_url.encode()).hexdigest()}"
                
                file_key = f"{folder_prefix}{fname}"
                self._download_and_upload(file_url, file_key, spider, item, is_main=False)
                
                item['file_path'] = f"s3://{self.bucket_name}/{folder_prefix}"
            
        except Exception as e:
            spider.logger.error(f"error processing files for {ref_number}: {e}")
            
        return item

    def _download_and_upload(self, url, filename, spider, item, is_main=False):
        try:
            spider.logger.debug(f"downloading {url}")
            response = requests.get(url, verify=False, timeout=30)
            
            if response.status_code == 200:
                data = io.BytesIO(response.content)
                content_type = response.headers.get('Content-Type', 'application/octet-stream')
                
                if is_main:
                    file_hash = hashlib.sha256(response.content).hexdigest()
                    item['file_hash'] = file_hash

                self.s3_client.upload_fileobj(
                    data,
                    self.bucket_name,
                    filename,
                    ExtraArgs={'ContentType': content_type}
                )
                spider.logger.debug(f"uploaded to s3://{self.bucket_name}/{filename}")
            else:
                spider.logger.warning(f"failed to download {url}: status {response.status_code}")
        except Exception as e:
            spider.logger.error(f"failed to upload {url}: {e}")
