import csv
from typing import IO, List, Dict
from io import TextIOWrapper
import logging
from .persistence.json_repo import JSONRepository
from .core.config import get_data_file_path
from .core.error_tracking import get_error_tracker
from .core.notifications import get_notification_service
import os
from datetime import datetime
import json

logger = logging.getLogger(__name__)


def parse_csv_file(file_obj: IO) -> List[Dict[str, str]]:
    wrapper = TextIOWrapper(file_obj, encoding="utf-8")
    reader = csv.DictReader(wrapper)
    rows = [row for row in reader]
    wrapper.detach()
    return rows


def background_bulk_enroll(upload_file, course_id: str):
    error_tracker = get_error_tracker()
    notification_service = get_notification_service()
    
    try:
        repo = JSONRepository(get_data_file_path())
        rows = parse_csv_file(upload_file)
        logger.info(f"Processing bulk enrollment for course {course_id}: {len(rows)} rows")
        
        report = repo.bulk_enroll(course_id, rows)
        
        # Log success
        logger.info(
            f"Bulk enrollment completed: {report['enrolled']} enrolled, "
            f"{report['skipped']} skipped, {len(report['errors'])} errors"
        )
        
        # Generate report file
        data_dir = os.path.dirname(get_data_file_path())
        filename = f"bulk_enroll_report_{course_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.json"
        path = os.path.join(data_dir, filename)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2)
        
        # Notify if there were errors
        if report["errors"]:
            notification_service.notify_error(
                error_type="BulkEnrollment",
                message=f"Bulk enrollment for course {course_id} completed with {len(report['errors'])} errors",
                error_code="BULK_ENROLLMENT_PARTIAL_FAILURE",
                details={"enrolled": report["enrolled"], "skipped": report["skipped"], "errors": len(report["errors"])},
                severity="WARNING",
            )
    
    except Exception as e:
        error_record = error_tracker.log_error(
            "BulkEnrollmentTask",
            f"Background bulk enrollment failed for course {course_id}: {str(e)}",
            "BULK_ENROLLMENT_TASK_FAILED",
            {"course_id": course_id},
            e,
        )
        
        # Notify critical failure
        notification_service.notify_error(
            error_type="BulkEnrollmentTask",
            message=error_record["message"],
            error_code=error_record["error_code"],
            details=error_record["details"],
            severity="CRITICAL",
        )
