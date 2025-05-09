import streamlit as st
import yfinance as yf
import json
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
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

def get_gsheet_client():
    credentials = {
        "type": st.secrets["gspread"]["type"],
        "project_id": st.secrets["gspread"]["project_id"],
        "private_key_id": st.secrets["gspread"]["private_key_id"],
        "private_key": st.secrets["gspread"]["private_key"].replace("\\n", "\n"),
        "client_email": st.secrets["gspread"]["client_email"],
        "client_id": st.secrets["gspread"]["client_id"],
        "token_uri": st.secrets["gspread"]["token_uri"],
    }
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials, scope)
    return gspread.authorize(creds)

def load_tickers():
    try:
        gc = get_gsheet_client()
        sheet_id = st.secrets["gspread"]["sheet_id"]
        sheet = gc.open_by_key(sheet_id)
        worksheet = sheet.sheet1
        values = worksheet.col_values(1)
        tickers = [t.upper().strip() for t in values[1:] if t.strip()]
        return list(set(tickers))
    except Exception as e:
        st.error("Error loading tickers. Showing fallback tickers.")
        return ["OKLO", "HOOD", "TSLA", "PLTR", "TEM"]




def add_ticker(new_ticker):
    if not new_ticker:
        return False, "Ticker cannot be empty"
    
    new_ticker = new_ticker.strip().upper()
    
    # Basic validation
    if not new_ticker.isalnum():
        return False, f"Invalid ticker format: {new_ticker}"
    
    try:
        gc = get_gsheet_client()
        sheet = gc.open_by_key(st.secrets["gspread"]["sheet_id"]).sheet1
        existing = load_tickers()
        
        if new_ticker in existing:
            return False, f"Ticker {new_ticker} already in list"
            
        sheet.append_row([new_ticker])
        return True, f"Added {new_ticker} successfully!"
    except Exception as e:
        return False, f"Error adding ticker: {str(e)}"

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
        # Add the ticker using the Google Sheets function
        success, message = add_ticker(new_ticker)
        
        if success:
            st.success(message)
            # Show current tickers in an expander
            with st.expander("Current Tickers"):
                updated_tickers = load_tickers()
                st.write(updated_tickers)
            
            # Force reload to update the dropdown
            st.cache_data.clear()
            st.rerun()
        else:
            st.error(message)

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
