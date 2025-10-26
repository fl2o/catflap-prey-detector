"""Google Cloud Storage sync module for uploading and managing detection images."""
import logging
import asyncio
from datetime import datetime
from pathlib import Path

from google.cloud import storage

from catflap_prey_detector.detection.config import cloud_sync_config

logger = logging.getLogger(__name__)


class CloudStorageSync:
    """Handles syncing local directories to Google Cloud Storage."""
    
    def __init__(self):
        self.bucket_name = cloud_sync_config.bucket_name
        self.upload_batch_size = cloud_sync_config.upload_batch_size
        self._client: storage.Client | None = None
        self._bucket: storage.Bucket | None = None
        
        if not self._verify_bucket_access_sync():
            raise ValueError(f"Cannot access bucket {self.bucket_name}")
        
    @property
    def client(self) -> storage.Client:
        """Lazy-load GCS client."""
        if self._client is None:
            self._client = storage.Client()
        return self._client
    
    @property
    def bucket(self) -> storage.Bucket:
        """Lazy-load GCS bucket."""
        if self._bucket is None:
            self._bucket = self.client.bucket(self.bucket_name)
        return self._bucket
    
    def _get_cloud_path(self, local_path: Path, base_dir: Path, cloud_prefix: str) -> str:
        """Generate cloud storage path from local path."""
        relative_path = local_path.relative_to(base_dir)
        return f"{cloud_prefix}/{relative_path}"
    
    async def upload_file(self, local_path: Path, cloud_path: str) -> bool:
        """Upload a single file to cloud storage."""
        try:
            blob = self.bucket.blob(cloud_path)
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, blob.upload_from_filename, str(local_path))
            
            logger.info(f"Uploaded {local_path} to gs://{self.bucket_name}/{cloud_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to upload {local_path}: {e}")
            return False
    
    async def sync_directory(
        self, 
        local_dir: str, 
        cloud_prefix: str,
        file_pattern: str = "*.jpg",
        max_files: int | None = None
    ) -> dict[str, any]:
        """
        Sync a local directory to cloud storage.
        
        Args:
            local_dir: Local directory path to sync
            cloud_prefix: Prefix for cloud storage paths
            file_pattern: Glob pattern for files to sync
            max_files: Maximum number of files to process
            
        Returns:
            Dictionary with sync statistics
        """
        local_path = Path(local_dir)
        if not local_path.exists():
            logger.warning(f"Directory {local_dir} does not exist")
            return {"uploaded": 0, "failed": 0}
        
        files = list(local_path.glob(file_pattern))
        if max_files:
            files = files[:max_files]
        
        stats = {"uploaded": 0, "failed": 0}
        
        for batch_start in range(0, len(files), self.upload_batch_size):
            batch_files = files[batch_start:batch_start + self.upload_batch_size]
            
            tasks = []
            for file_path in batch_files:
                cloud_path = self._get_cloud_path(file_path, local_path, cloud_prefix)
                tasks.append(self.upload_file(file_path, cloud_path))
            
            results = await asyncio.gather(*tasks)
            
            for file_path, success in zip(batch_files, results):
                if success:
                    stats["uploaded"] += 1
                else:
                    stats["failed"] += 1
        
        logger.info(f"Sync completed for {local_dir}: {stats}")
        return stats
    
    
    def _verify_bucket_access_sync(self) -> bool:
        """Verify that we can access the configured bucket (synchronous)."""
        try:
            if not self.bucket.exists():
                logger.error(f"Bucket {self.bucket_name} does not exist")
                return False
            
            test_blob = self.bucket.blob("_test_access.txt")
            test_blob.upload_from_string(f"Access test at {datetime.now().isoformat()}")
            test_blob.delete()
            
            logger.info(f"Successfully verified access to bucket {self.bucket_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to verify bucket access: {e}")
            return False


if __name__ == "__main__":
    storage_sync = CloudStorageSync()
    print('done')
