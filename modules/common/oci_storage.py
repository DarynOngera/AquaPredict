"""OCI Object Storage integration for AquaPredict."""

import oci
import os
import logging
from typing import List, Optional, BinaryIO
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OCIStorageClient:
    """OCI Object Storage client for data, models, and reports."""
    
    def __init__(self):
        """Initialize OCI Object Storage client."""
        # Load OCI config
        config_file = os.getenv("OCI_CONFIG_FILE", "~/.oci/config")
        config_profile = os.getenv("OCI_CONFIG_PROFILE", "DEFAULT")
        
        self.config = oci.config.from_file(config_file, config_profile)
        self.object_storage = oci.object_storage.ObjectStorageClient(self.config)
        self.namespace = self.object_storage.get_namespace().data
        
        logger.info(f"OCI Object Storage initialized (namespace: {self.namespace})")
    
    def upload_file(
        self,
        bucket_name: str,
        object_name: str,
        file_path: str,
        metadata: Optional[dict] = None
    ) -> str:
        """
        Upload file to OCI Object Storage.
        
        Returns:
            Object URL
        """
        try:
            with open(file_path, 'rb') as file:
                self.object_storage.put_object(
                    namespace_name=self.namespace,
                    bucket_name=bucket_name,
                    object_name=object_name,
                    put_object_body=file,
                    metadata=metadata or {}
                )
            
            logger.info(f"Uploaded {object_name} to {bucket_name}")
            
            return f"oci://{bucket_name}@{self.namespace}/{object_name}"
        
        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            raise
    
    def upload_bytes(
        self,
        bucket_name: str,
        object_name: str,
        data: bytes,
        metadata: Optional[dict] = None
    ) -> str:
        """
        Upload bytes to OCI Object Storage.
        
        Returns:
            Object URL
        """
        try:
            self.object_storage.put_object(
                namespace_name=self.namespace,
                bucket_name=bucket_name,
                object_name=object_name,
                put_object_body=data,
                metadata=metadata or {}
            )
            
            logger.info(f"Uploaded {object_name} to {bucket_name}")
            
            return f"oci://{bucket_name}@{self.namespace}/{object_name}"
        
        except Exception as e:
            logger.error(f"Error uploading bytes: {e}")
            raise
    
    def download_file(
        self,
        bucket_name: str,
        object_name: str,
        file_path: str
    ):
        """Download file from OCI Object Storage."""
        try:
            response = self.object_storage.get_object(
                namespace_name=self.namespace,
                bucket_name=bucket_name,
                object_name=object_name
            )
            
            with open(file_path, 'wb') as file:
                for chunk in response.data.raw.stream(1024 * 1024, decode_content=False):
                    file.write(chunk)
            
            logger.info(f"Downloaded {object_name} from {bucket_name}")
        
        except Exception as e:
            logger.error(f"Error downloading file: {e}")
            raise
    
    def download_bytes(
        self,
        bucket_name: str,
        object_name: str
    ) -> bytes:
        """Download file as bytes from OCI Object Storage."""
        try:
            response = self.object_storage.get_object(
                namespace_name=self.namespace,
                bucket_name=bucket_name,
                object_name=object_name
            )
            
            return response.data.content
        
        except Exception as e:
            logger.error(f"Error downloading bytes: {e}")
            raise
    
    def list_objects(
        self,
        bucket_name: str,
        prefix: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[dict]:
        """List objects in bucket."""
        try:
            response = self.object_storage.list_objects(
                namespace_name=self.namespace,
                bucket_name=bucket_name,
                prefix=prefix,
                limit=limit
            )
            
            objects = []
            for obj in response.data.objects:
                objects.append({
                    'name': obj.name,
                    'size': obj.size,
                    'time_created': obj.time_created.isoformat() if obj.time_created else None,
                    'time_modified': obj.time_modified.isoformat() if obj.time_modified else None,
                    'md5': obj.md5
                })
            
            return objects
        
        except Exception as e:
            logger.error(f"Error listing objects: {e}")
            raise
    
    def delete_object(
        self,
        bucket_name: str,
        object_name: str
    ):
        """Delete object from bucket."""
        try:
            self.object_storage.delete_object(
                namespace_name=self.namespace,
                bucket_name=bucket_name,
                object_name=object_name
            )
            
            logger.info(f"Deleted {object_name} from {bucket_name}")
        
        except Exception as e:
            logger.error(f"Error deleting object: {e}")
            raise
    
    def get_presigned_url(
        self,
        bucket_name: str,
        object_name: str,
        expiration_hours: int = 24
    ) -> str:
        """
        Generate presigned URL for temporary access.
        
        Returns:
            Presigned URL
        """
        try:
            # Create PAR (Pre-Authenticated Request)
            par_details = oci.object_storage.models.CreatePreauthenticatedRequestDetails(
                name=f"temp-access-{datetime.now().timestamp()}",
                object_name=object_name,
                access_type="ObjectRead",
                time_expires=datetime.utcnow() + timedelta(hours=expiration_hours)
            )
            
            par = self.object_storage.create_preauthenticated_request(
                namespace_name=self.namespace,
                bucket_name=bucket_name,
                create_preauthenticated_request_details=par_details
            )
            
            # Construct full URL
            region = self.config['region']
            url = f"https://objectstorage.{region}.oraclecloud.com{par.data.access_uri}"
            
            logger.info(f"Generated presigned URL for {object_name}")
            
            return url
        
        except Exception as e:
            logger.error(f"Error generating presigned URL: {e}")
            raise
    
    def get_object_metadata(
        self,
        bucket_name: str,
        object_name: str
    ) -> dict:
        """Get object metadata."""
        try:
            response = self.object_storage.head_object(
                namespace_name=self.namespace,
                bucket_name=bucket_name,
                object_name=object_name
            )
            
            return {
                'content_length': response.headers.get('Content-Length'),
                'content_type': response.headers.get('Content-Type'),
                'etag': response.headers.get('ETag'),
                'last_modified': response.headers.get('Last-Modified'),
                'metadata': dict(response.headers)
            }
        
        except Exception as e:
            logger.error(f"Error getting metadata: {e}")
            raise


class DataStorageManager:
    """High-level manager for AquaPredict data storage."""
    
    def __init__(self):
        self.storage = OCIStorageClient()
        self.buckets = {
            'raw': 'aquapredict-data-raw',
            'processed': 'aquapredict-data-processed',
            'models': 'aquapredict-models',
            'reports': 'aquapredict-reports'
        }
    
    def save_raw_data(
        self,
        dataset_name: str,
        date: str,
        file_path: str
    ) -> str:
        """Save raw GEE data."""
        object_name = f"{dataset_name}/{date}/{os.path.basename(file_path)}"
        return self.storage.upload_file(
            self.buckets['raw'],
            object_name,
            file_path,
            metadata={'dataset': dataset_name, 'date': date}
        )
    
    def save_processed_features(
        self,
        region: str,
        date: str,
        file_path: str
    ) -> str:
        """Save processed features."""
        object_name = f"features/{region}/{date}/{os.path.basename(file_path)}"
        return self.storage.upload_file(
            self.buckets['processed'],
            object_name,
            file_path,
            metadata={'region': region, 'date': date}
        )
    
    def save_model(
        self,
        model_name: str,
        version: str,
        file_path: str
    ) -> str:
        """Save trained model."""
        object_name = f"{model_name}/{version}/{os.path.basename(file_path)}"
        return self.storage.upload_file(
            self.buckets['models'],
            object_name,
            file_path,
            metadata={'model': model_name, 'version': version}
        )
    
    def load_model(
        self,
        model_name: str,
        version: str,
        filename: str,
        local_path: str
    ):
        """Load trained model."""
        object_name = f"{model_name}/{version}/{filename}"
        self.storage.download_file(
            self.buckets['models'],
            object_name,
            local_path
        )
    
    def save_report(
        self,
        report_id: str,
        report_type: str,
        file_path: str
    ) -> str:
        """Save generated report."""
        object_name = f"{report_type}/{report_id}/{os.path.basename(file_path)}"
        return self.storage.upload_file(
            self.buckets['reports'],
            object_name,
            file_path,
            metadata={'report_id': report_id, 'type': report_type}
        )
    
    def get_report_url(
        self,
        report_id: str,
        report_type: str,
        filename: str
    ) -> str:
        """Get presigned URL for report download."""
        object_name = f"{report_type}/{report_id}/{filename}"
        return self.storage.get_presigned_url(
            self.buckets['reports'],
            object_name,
            expiration_hours=24
        )
