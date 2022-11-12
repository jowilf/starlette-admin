import os

from libcloud.storage.base import StorageDriver
from libcloud.storage.providers import get_driver
from libcloud.storage.types import ContainerDoesNotExistError, Provider
from sqlalchemy_file.storage import StorageManager

from .config import UPLOAD_DIR


def get_or_create_container(driver: StorageDriver, container_name: str):
    try:
        return driver.get_container(container_name)
    except ContainerDoesNotExistError:
        """This will just create a new directory inside the base directory for local storage."""
        return driver.create_container(container_name)


def configure_storage():
    os.makedirs(UPLOAD_DIR, 0o777, exist_ok=True)  # Create Base directory
    cls = get_driver(Provider.LOCAL)
    driver = cls(UPLOAD_DIR)
    """
    You are free to use any storage providers supported by apache-libcloud
    
    
    Example with S3
    ```python
    cls = get_driver(Provider.S3)
    driver = cls("api key", "api secret key")
    ```
    
    Example with minio
    ```python
    cls = get_driver(Provider.MINIO)
    driver = cls("minioadmin", "minioadmin", secure=False, host="127.0.0.1", port=9000)
    ```
    
    See https://libcloud.readthedocs.io/en/stable/storage/supported_providers.html for more
    """
    StorageManager.add_storage("default", get_or_create_container(driver, "bin"))
    StorageManager.add_storage("cover", get_or_create_container(driver, "book-cover"))
    StorageManager.add_storage(
        "documents", get_or_create_container(driver, "book-docs")
    )
    StorageManager.add_storage("avatar", get_or_create_container(driver, "avatars"))
