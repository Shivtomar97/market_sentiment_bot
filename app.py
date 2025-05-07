import streamlit as st
import yfinance as yf
import json
import os
from dotenv import load_dotenv
from news_fetcher import get_news
from summarizer import summarize
from telegram_alerts import send_telegram_message

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
            combined_lines.append(f"🔹 *{title}*  ")
            combined_lines.append(f"🧠 {sentiment_text} {action_text}".strip())
            combined_lines.append("")  # blank line

    # Send combined Telegram alert after processing all articles
    if len(combined_lines) > 2:
        combined_message = "\n".join(combined_lines)
        send_telegram_message(combined_message)

# Market Events Calendar
st.subheader("📅 Upcoming Market Events")
with open("calendar_events.json") as f:
    events = json.load(f)
    for event in events:
        st.markdown(f"- **{event['date']}**: {event['event']} ({event['impact']})")
