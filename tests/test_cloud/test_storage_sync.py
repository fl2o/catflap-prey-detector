import pytest
from conftest import skip_if_no_gcs
from catflap_prey_detector.cloud.storage_sync import CloudStorageSync


def test_get_cloud_path(test_images_dir):
    if not skip_if_no_gcs:
        pytest.skip("Skipping: GOOGLE_APPLICATION_CREDENTIALS not set")
    
    sync = CloudStorageSync()
    local_path = test_images_dir / "cat_no_prey.jpeg"
    base_dir = test_images_dir
    cloud_prefix = "detection_images"
    
    cloud_path = sync._get_cloud_path(local_path, base_dir, cloud_prefix)
    
    expected_cloud_path = "detection_images/cat_no_prey.jpeg"
    assert cloud_path == expected_cloud_path


@skip_if_no_gcs
@pytest.mark.asyncio
async def test_sync_directory_nonexistent():
    sync = CloudStorageSync()
    
    stats = await sync.sync_directory(
        "/tmp/nonexistent_directory_for_testing",
        "test_prefix",
        "*.jpg"
    )
    
    expected_uploaded = 0
    expected_failed = 0
    
    assert stats["uploaded"] == expected_uploaded
    assert stats["failed"] == expected_failed

