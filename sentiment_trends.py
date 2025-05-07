import pandas as pd
import matplotlib.pyplot as plt

def plot_sentiment_trend(log_path: str = "sentiment_log.csv", ticker: str = "OKLO"):
    """
    Read the sentiment log CSV, filter by ticker, and plot a stacked bar chart
    of sentiment counts per day using pandas and matplotlib.
    """
    # Load data
    try:
        df = pd.read_csv(log_path, parse_dates=['date'])
    except FileNotFoundError:
        print(f"Log file not found: {log_path}")
        return None

    # Filter for the specified ticker
    df = df[df['ticker'] == ticker]
    if df.empty:
        print(f"No sentiment data available for ticker: {ticker}")
        return None

    # Group by date and sentiment, count occurrences
    counts = df.groupby(['date', 'sentiment']).size().unstack(fill_value=0)

    # Plot stacked bar chart
    fig, ax = plt.subplots(figsize=(10, 6))
    counts.plot(kind='bar', stacked=True, ax=ax)

    ax.set_title(f"Sentiment Trend for {ticker}")
    ax.set_xlabel("Date")
    ax.set_ylabel("Count")
    ax.legend(title="Sentiment")

    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

    return fig 