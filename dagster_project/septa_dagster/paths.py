import os

DEFAULT_RAW_DATA_PATH = "/app/data/raw"


def raw_data_path() -> str:
    return os.environ.get("RAW_DATA_PATH", DEFAULT_RAW_DATA_PATH)
