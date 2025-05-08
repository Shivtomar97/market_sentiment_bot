import pandas as pd
import plotly.express as px
from pandas.errors import EmptyDataError


def plot_sentiment_trend(log_path: str = "sentiment_log.csv", ticker: str = "OKLO"):
    """
    Read the sentiment log CSV, filter by ticker, and plot an interactive stacked bar chart
    of sentiment counts per day using Plotly Express.
    """
    # Load data, handle missing or empty files
    try:
        df = pd.read_csv(log_path, parse_dates=["date"])
    except FileNotFoundError:
        print(f"Log file not found: {log_path}")
        return None
    except EmptyDataError:
        print(f"No data to parse from log file: {log_path}")
        return None

    # Coerce 'date' column to datetime and drop invalid entries
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date'])
    if df.empty:
        print(f"No valid date records found in log file: {log_path}")
        return None

    # Filter for the specified ticker
    df = df[df['ticker'] == ticker]
    if df.empty:
        print(f"No sentiment data available for ticker: {ticker}")
        return None

    # Exclude 'unknown' sentiments
    df = df[df['sentiment'] != 'unknown']
    if df.empty:
        print(f"No known sentiment data available for ticker: {ticker}")
        return None

    # Filter to only last 7 days of data
    last_week = pd.Timestamp.now() - pd.Timedelta(days=7)
    df = df[df['date'] >= last_week]
    if df.empty:
        print(f"No recent sentiment data (last 7 days) available for ticker: {ticker}")
        return None

    # Group by date and sentiment, count occurrences
    grouped = df.groupby(["date", "sentiment"]).size().reset_index(name="count")

    # Define order and colors for consistency
    sentiment_order = ["bullish", "neutral", "bearish", "unknown"]
    color_map = {
        'bullish': '#2ca02c',
        'neutral': '#ff7f0e',
        'bearish': '#d62728',
        'unknown': '#7f7f7f'
    }

    # Build title with date range for the last 7 days
    start_date = df['date'].min().date()
    end_date = df['date'].max().date()
    # Format dates as 'Month Day'
    date_range_str = f"{start_date.strftime('%B %d')} – {end_date.strftime('%B %d')}"
    title_text = f"Sentiment Trend for {ticker} ({date_range_str})"
    
    # Build the Plotly Express figure
    fig = px.bar(
        grouped,
        x="date",
        y="count",
        color="sentiment",
        category_orders={"sentiment": sentiment_order},
        color_discrete_map=color_map,
        title=title_text,
        labels={"count": "Count", "date": "Date", "sentiment": "Sentiment"}
    )

    fig.update_layout(
        barmode="stack",
        xaxis_tickformat="%Y-%m-%d",
        legend_title_text="Sentiment",
        margin=dict(l=40, r=40, t=80, b=40)
    )

    return fig 