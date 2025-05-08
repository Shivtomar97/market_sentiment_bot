import os
import csv
from datetime import date

def get_store_file(source: str) -> str:
    """Return the CSV filename for the given source."""
    return f"processed_{source.lower()}.csv"

def is_processed(url: str, source: str) -> bool:
    """Check if the given URL has already been processed for the given source."""
    file_path = get_store_file(source)
    if not os.path.isfile(file_path):
        return False
    try:
        with open(file_path, newline='') as f:
            reader = csv.reader(f)
            for row in reader:
                if row and row[0] == url:
                    return True
    except Exception:
        return False
    return False

def mark_processed(url: str, source: str, process_date: date = None):
    """Mark the given URL as processed for the given source, recording the date."""
    if process_date is None:
        process_date = date.today()
    file_path = get_store_file(source)
    write_header = not os.path.isfile(file_path) or os.path.getsize(file_path) == 0
    with open(file_path, 'a', newline='') as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(['url', 'date'])
        writer.writerow([url, process_date.isoformat()]) 