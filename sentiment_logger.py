import os
import csv
from datetime import date

def log_sentiment(ticker: str, sentiment: str, source: str, log_date=None, file_path: str = None):
    """
    Append the sentiment record to a CSV file named by source (e.g., sentiment_log_newsapi.csv).
    source: identifier used to name the logfile.
    log_date: a datetime.date; defaults to today.
    file_path: optional override of the CSV path.
    """
    # Determine the date to log
    if log_date is None:
        log_date = date.today()
    # Validate log_date is a date
    if not isinstance(log_date, date):
        raise ValueError("log_date must be a datetime.date instance")
    # Determine the CSV file path based on source if not provided
    if file_path is None:
        file_path = f"sentiment_log_{source.lower()}.csv"
    write_header = not os.path.isfile(file_path) or os.path.getsize(file_path) == 0
    with open(file_path, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        if write_header:
            writer.writerow(['date', 'ticker', 'sentiment'])
        writer.writerow([log_date.isoformat(), ticker, sentiment]) 