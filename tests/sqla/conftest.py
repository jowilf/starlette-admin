import base64
import os
import tempfile

import pytest

os.environ["SQLA_ENGINE"] = os.environ.get(
    "SQLA_ENGINE", "sqlite:///test.db?check_same_thread=False"
)
os.environ["SQLA_ASYNC_ENGINE"] = os.environ.get(
    "SQLA_ASYNC_ENGINE", "sqlite+aiosqlite:////tmp/test.db?check_same_thread=False"
)


@pytest.fixture
def fake_image_content():
    return base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAAXNSR0IArs4c6QAAAHNJREFUKFOdkLEKwCAMRM/JwUFwdPb"
        "/v8RPEDcdBQcHJyUt0hQ6hGY6Li8XEhVjXM45aK3xVXNOtNagcs6LRAgB1toX23tHSgkUpEopyxhzGRw"
        "+EHljjBv03oM3KJYP1lofkJoHJs3T/4Gi1aJjxO+RPnwDur2EF1gNZukAAAAASUVORK5CYII="
    )


@pytest.fixture
def fake_image(fake_image_content):
    file = tempfile.NamedTemporaryFile(suffix=".png")
    file.write(fake_image_content)
    file.seek(0)
    return file


@pytest.fixture
def fake_invalid_image():
    file = tempfile.NamedTemporaryFile(suffix=".png")
    file.write(b"Pass through content type validation")
    file.seek(0)
    return file


@pytest.fixture
def fake_empty_file():
    file = tempfile.NamedTemporaryFile()
    file.seek(0)
    return file
