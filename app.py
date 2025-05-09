import streamlit as st
import yfinance as yf
import json
import os
from dotenv import load_dotenv
from news_fetcher import get_news, get_rss_news
from summarizer import summarize
from telegram_alerts import send_telegram_message
from sentiment_logger import log_sentiment
from sentiment_trends import plot_sentiment_trend
from datetime import datetime, date
from processed_store import is_processed, mark_processed

def extract_sentiment_keyword(text: str) -> str:
    """
    Extract the primary sentiment keyword from the summary text.
    """
    lower = text.lower()
    for kw in ('bullish', 'bearish', 'neutral'):
        if kw in lower:
            return kw
    return 'unknown'

def main():
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

    # News Section (choose data source)
    st.subheader(f"🔎 News and Sentiment for {selected_ticker}")
    col1, col2 = st.columns(2)
    # Render both buttons and capture their clicks
    newsapi_clicked = col1.button("Fetch via NewsAPI")
    rss_clicked = col2.button("Fetch via RSS")

    if newsapi_clicked:
        articles = get_news(selected_ticker)
        source = "NewsAPI"
    elif rss_clicked:
        articles = get_rss_news(selected_ticker)
        source = "RSS"
    else:
        articles = None
        source = None

    if articles is None:
        st.write("Select a source to fetch news.")
    elif not articles:
        st.write(f"No articles found via {source}.")
    else:
        combined_lines = [f"📰 ${selected_ticker} ({source})", ""]
        for article in articles:
            title = article.get("title", "No title")
            url = article.get("url")
            st.markdown(f"### {title}")
            st.caption(f"{article.get('source','Unknown source')} • {article.get('publishedAt','')}")
            if url:
                st.markdown(f"[🔗 Read full article]({url})", unsafe_allow_html=True)
            description = article.get("description") or article.get("content") or "No summary available."
            summary = summarize(description, selected_ticker)
            st.success(summary)
            sentiment_key = extract_sentiment_keyword(summary)
            pub_str = article.get("publishedAt", "")
            # Only log and mark processed if this URL hasn't been seen for this source
            already = is_processed(url, source) if url else False
            if url and not already:
                try:
                    pub_date = datetime.fromisoformat(pub_str.replace("Z", ""))
                    log_sentiment(selected_ticker, sentiment_key, source, log_date=pub_date.date())
                except Exception:
                    log_sentiment(selected_ticker, sentiment_key, source)
                # Add to Telegram batch
                combined_lines.append(f"🔹 *{title}*  ")
                combined_lines.append(f"🧠 {sentiment_key}".strip())
                combined_lines.append("")  # blank line
                # Mark this URL as processed to avoid duplicates
                mark_processed(url, source, process_date=pub_date.date())

        if len(combined_lines) > 2:
            send_telegram_message("\n".join(combined_lines))
        # Sentiment Trend Plot (runs only after articles fetched and processed)
        st.subheader("📈 Sentiment Trend")
        log_path = f"sentiment_log_{source.lower()}.csv"
        fig = plot_sentiment_trend(log_path=log_path, ticker=selected_ticker)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write(f"No sentiment data to display for {source}.")

    # Market Events Calendar
    st.subheader("📅 Upcoming Market Events")
    with open("calendar_events.json") as f:
        events = json.load(f)
        for event in events:
            st.markdown(f"- **{event['date']}**: {event['event']} ({event['impact']})")

if __name__ == "__main__":
    main()
