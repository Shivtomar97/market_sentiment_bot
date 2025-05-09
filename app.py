import streamlit as st
import yfinance as yf
import json
import os
import csv
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

    # Create a container for logs at the top for debugging
    log_container = st.empty()
    def show_logs(title, logs):
        """Display logs directly in the UI for debugging"""
        with log_container.container():
            st.subheader(f"Debug Logs: {title}")
            st.json(logs)
            st.divider()

    # Debug info for ticker management (moved from sidebar)
    ticker_debug = st.empty()

    # Function to load tickers from CSV - simplified
    def load_tickers():
        default_tickers = ["OKLO", "HOOD", "TSLA", "PLTR", "TEM"]
        ticker_file = "tickers.csv"
        
        # Create initial file if it doesn't exist
        if not os.path.exists(ticker_file):
            with open(ticker_file, 'w', newline='') as f:
                writer = csv.writer(f)
                for ticker in default_tickers:
                    writer.writerow([ticker])
            return default_tickers
        
        # Read existing tickers
        try:
            with open(ticker_file, 'r', newline='') as f:
                reader = csv.reader(f)
                tickers = [row[0] for row in reader if row and row[0]]
            return tickers if tickers else default_tickers
        except Exception as e:
            st.error(f"Error loading tickers: {str(e)}")
            return default_tickers

    # Load tickers
    tickers = load_tickers()
    
    # Main ticker selection in the main area with quick add button
    st.subheader("📊 Ticker Selection")
    # Use a more balanced column layout
    left, right = st.columns([1, 1])
    
    # Left column for ticker selection
    with left:
        # Add label manually for consistent alignment with Add New Ticker
        st.write("Select a Ticker:")
        selected_ticker = st.selectbox("Select Ticker", tickers, label_visibility="collapsed")
    
    # Right column for adding new tickers with better alignment
    with right:
        # Add label manually to match the positioning of the selectbox label
        st.write("Add New Ticker:")
        # Create columns for the input and button on the same row
        input_col, btn_col = st.columns([2, 1])
        with input_col:
            new_ticker = st.text_input("New Ticker", placeholder="AAPL", label_visibility="collapsed")
        with btn_col:
            add_btn = st.button("Add Ticker", type="primary", use_container_width=True)

    # Handle the add ticker logic directly
    if add_btn and new_ticker:
        # Format and validate the ticker
        new_ticker = new_ticker.strip().upper()
        
        # Basic validation
        if not new_ticker:
            st.error("Ticker cannot be empty")
        elif not new_ticker.isalnum():
            st.error(f"Invalid ticker format: {new_ticker}")
        elif new_ticker in tickers:
            st.error(f"Ticker {new_ticker} already in list")
        else:
            # Add the ticker directly
            try:
                # Add to the list
                tickers.append(new_ticker)
                
                # Write all tickers to file
                with open("tickers.csv", 'w', newline='') as f:
                    writer = csv.writer(f)
                    for ticker in tickers:
                        writer.writerow([ticker])
                
                # Show success and details in expander
                st.success(f"Added {new_ticker} successfully!")
                
                with st.expander("Debug Info"):
                    st.write("Current tickers:", tickers)
                    st.write("File path:", os.path.join(os.getcwd(), "tickers.csv"))
                    st.write("File exists:", os.path.exists("tickers.csv"))
                    
                    with open("tickers.csv", 'r') as f:
                        content = f.read()
                        st.code(content)
                
                # Force reload
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Error adding ticker: {str(e)}")
                st.write("Please check the ticker format and try again.")

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
