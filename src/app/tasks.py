import csv
from typing import IO, List, Dict
from io import TextIOWrapper
from .persistence.json_repo import JSONRepository
from .core.config import get_data_file_path
import os
from datetime import datetime
import json

def parse_csv_file(file_obj: IO) -> List[Dict[str, str]]:
    wrapper = TextIOWrapper(file_obj, encoding="utf-8")
    reader = csv.DictReader(wrapper)
    rows = [row for row in reader]
    wrapper.detach()
    return rows

def background_bulk_enroll(upload_file, course_id: str):
    repo = JSONRepository(get_data_file_path())
    rows = parse_csv_file(upload_file)
    report = repo.bulk_enroll(course_id, rows)
    data_dir = os.path.dirname(get_data_file_path())
    filename = f"bulk_enroll_report_{course_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.json"
    path = os.path.join(data_dir, filename)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
