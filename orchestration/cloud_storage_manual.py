
from pathlib import Path

from orchestration.cloud_storage import (
    delete_file,
    download_file,
    list_objects,
    object_exists,
    upload_file,
)


def main():
    test_file = Path(
        "orchestration/cloud_storage_test.txt"
    )

    test_file.write_text(
        "Weather Intelligence Platform cloud storage test.\n",
        encoding="utf-8",
    )

    object_key = "test/cloud_storage_test.txt"

    download_path = Path(
        "orchestration/cloud_storage_downloaded.txt"
    )

    print("\n=== CLOUD STORAGE TEST ===\n")

    print("1. Upload")
    upload_file(test_file, object_key)

    print("\n2. Check object exists")
    exists = object_exists(object_key)
    print(f"Object exists: {exists}")

    print("\n3. List test objects")
    objects = list_objects(prefix="test/")

    for obj in objects:
        print(f" - {obj}")

    print("\n4. Download")
    download_file(object_key, download_path)

    print(
        f"Downloaded content: "
        f"{download_path.read_text(encoding='utf-8').strip()}"
    )

    print("\n=== TEST PASSED ===")
    print(
        "The test object has intentionally "
        "been left in S3."
    )


if __name__ == "__main__":
    main()
