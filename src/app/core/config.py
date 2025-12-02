import os

def get_data_file_path() -> str:
    return os.getenv("DATA_FILE_PATH", "/data/lms_data.json")
