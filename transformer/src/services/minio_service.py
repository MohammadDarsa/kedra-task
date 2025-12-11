import io
import logging
import os
from urllib.parse import urlparse
from minio import Minio
from src.settings import Settings

logger = logging.getLogger(__name__)

class MinioService:
    def __init__(self):
        try:
            # this is important for it to work locally
            endpoint = Settings.MINIO_ENDPOINT.replace('http://', '').replace('https://', '')
            self.client = Minio(
                endpoint,
                access_key=Settings.MINIO_ACCESS_KEY,
                secret_key=Settings.MINIO_SECRET_KEY,
                secure=False
            )
            self._ensure_bucket(Settings.TARGET_BUCKET)
            logger.info("connected to minio")
        except Exception as e:
            logger.error(f"failed to connect to minio: {e}")
            raise

    def _ensure_bucket(self, bucket_name):
        if not self.client.bucket_exists(bucket_name):
            self.client.make_bucket(bucket_name)
            logger.info(f"created bucket: {bucket_name}")

    def get_file_content(self, file_path_s3):
        try:
            parsed = urlparse(file_path_s3)
            bucket_name = parsed.netloc
            object_name = parsed.path.lstrip('/')
            
            response = self.client.get_object(bucket_name, object_name)
            content = response.read()
            response.close()
            response.release_conn()
            return content, object_name
        except Exception as e:
            logger.error(f"error fetching file {file_path_s3}: {e}")
            return None, None

    def list_files(self, folder_path_s3):
        try:
            parsed = urlparse(folder_path_s3)
            bucket_name = parsed.netloc
            prefix = parsed.path.lstrip('/')
            if not prefix.endswith('/'):
                 prefix += '/'
            objects = self.client.list_objects(bucket_name, prefix=prefix, recursive=True)
            return [f"s3://{bucket_name}/{obj.object_name}" for obj in objects]
        except Exception as e:
            logger.error(f"error listing files in {folder_path_s3}: {e}")
            return []

    def upload_file(self, filename, content, content_type='application/octet-stream'):
        try:
            self.client.put_object(
                Settings.TARGET_BUCKET,
                filename,
                io.BytesIO(content),
                len(content),
                content_type=content_type
            )
            return f"s3://{Settings.TARGET_BUCKET}/{filename}"
        except Exception as e:
            logger.error(f"failed to upload {filename}: {e}")
            raise
