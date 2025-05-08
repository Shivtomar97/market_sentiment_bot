import os
import csv
from datetime import date

def log_sentiment(ticker: str, sentiment: str, file_path: str = 'sentiment_log.csv'):
    """Append the sentiment record to a CSV file with headers if needed."""
    write_header = not os.path.isfile(file_path) or os.path.getsize(file_path) == 0
    with open(file_path, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        if write_header:
            writer.writerow(['date', 'ticker', 'sentiment'])
        writer.writerow([date.today().isoformat(), ticker, sentiment]) 