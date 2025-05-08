import streamlit as st
import yfinance as yf
import json
import os
from dotenv import load_dotenv
from news_fetcher import get_news
from summarizer import summarize
from telegram_alerts import send_telegram_message
from sentiment_logger import log_sentiment
from sentiment_trends import plot_sentiment_trend
from datetime import datetime, date

def extract_sentiment_keyword(text: str) -> str:
    """
    Extract the primary sentiment keyword from the summary text.
    """
    lower = text.lower()
    for kw in ('bullish', 'bearish', 'neutral'):
        if kw in lower:
            return kw
    return 'unknown'

# Load environment variables
load_dotenv()

# Streamlit page setup
st.set_page_config(layout="wide")
st.title("📈 Market Strategy Bot")

# Ticker selection
tickers = ["OKLO", "HOOD", "TSLA", "PLTR", "TEM"]
selected_ticker = st.selectbox("Select a Ticker", tickers)

# Live Price Section
st.subheader(f"📊 Live Stock Price for {selected_ticker}")
ticker_data = yf.Ticker(selected_ticker)
price = ticker_data.history(period="1d")["Close"].iloc[-1]
st.metric(label=f"{selected_ticker} Current Price", value=f"${price:.2f}")

# News Section
st.subheader(f"🔎 News and Sentiment for {selected_ticker}")
articles = get_news(selected_ticker)

if not articles:
    st.write("No news articles found.")
else:
    # Initialize combined Telegram message lines
    combined_lines = [f"📰 ${selected_ticker}", ""]
    for article in articles:
        st.markdown(f"**{article['title']}**")
        st.caption(f"{article['source']} • {article['publishedAt']}")
        st.markdown(f"[Read more]({article['url']})")

        description = article.get("description") or article.get("content") or "No summary available."
        summary = summarize(description, selected_ticker)
        st.success(summary)
        # Collect for combined Telegram message
        if not summary.startswith("Error summarizing"):
            title = article.get("title", "No title")
            # Parse sentiment and action
            sentiment_text = summary
            action_text = ""
            if ";" in summary:
                parts = [p.strip() for p in summary.split(";", 1)]
                sentiment_text = parts[0]
                action_text = parts[1]
            elif "Suggested action:" in summary:
                parts = summary.split("Suggested action:", 1)
                sentiment_text = parts[0].strip()
                action_text = "Suggested action:" + parts[1].strip()
            # Only log if summary is non-empty and the article is from today
            pub_date_str = article.get("publishedAt", "")
            try:
                pub_date = datetime.fromisoformat(pub_date_str.replace("Z", ""))
                is_today = pub_date.date() == date.today()
            except:
                is_today = False
            if summary.strip() and is_today:
                sentiment_key = extract_sentiment_keyword(sentiment_text)
                log_sentiment(selected_ticker, sentiment_key)
            combined_lines.append(f"🔹 *{title}*  ")
            combined_lines.append(f"🧠 {sentiment_text} {action_text}".strip())
            combined_lines.append("")  # blank line

    # Send combined Telegram alert after processing all articles
    if len(combined_lines) > 2:
        combined_message = "\n".join(combined_lines)
        send_telegram_message(combined_message)

    # Sentiment Trend Plot
    st.subheader("📈 Sentiment Trend")
    fig = plot_sentiment_trend(log_path="sentiment_log.csv", ticker=selected_ticker)
    if fig:
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("No sentiment data to display.")

# Market Events Calendar
st.subheader("📅 Upcoming Market Events")
with open("calendar_events.json") as f:
    events = json.load(f)
    for event in events:
        st.markdown(f"- **{event['date']}**: {event['event']} ({event['impact']})")
