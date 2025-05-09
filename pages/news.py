import streamlit as st
from datetime import datetime, date, timedelta
from news_fetcher import get_rss_general_news
from summarizer import summarize
from app import extract_sentiment_keyword
from sentiment_logger import log_sentiment
from processed_store import is_processed, mark_processed

# Page title
st.title("📰 General Market News")
# Identifier for this page's logging source
page_source = "rss"

# Sidebar filters
st.sidebar.header("Filters")
sentiments = ["bullish", "neutral", "bearish"]
selected_sentiments = st.sidebar.multiselect(
    "Select sentiment to display", options=sentiments, default=sentiments
)
keyword = st.sidebar.text_input("Keyword filter (optional)", "")

@st.cache_data(ttl=3600)
def fetch_general_news():
    """
    Cached fetch of general market headlines via RSS.
    """
    return get_rss_general_news()

# Fetch general market news (cached)
articles = fetch_general_news()
if not articles:
    st.write("No general market news found.")
    st.stop()

# Analyze articles automatically
results = []
cutoff = datetime.utcnow() - timedelta(days=7)

for article in articles:
    title = article.get("title", "No title")
    description = article.get("description") or article.get("content") or ""
    article_source = article.get("source", "Unknown source")
    pub_str = article.get("publishedAt", "")
    try:
        pub_date = datetime.fromisoformat(pub_str.replace("Z", ""))
    except:
        continue
    # Only articles from the last 7 days
    if pub_date < cutoff:
        continue
    # Keyword filter
    if keyword and keyword.lower() not in (title + description).lower():
        continue

    summary = summarize(description, "market")
    sentiment = extract_sentiment_keyword(summary)
    # Log sentiment only for new articles
    url = article.get("url")
    already = is_processed(url, page_source) if url else False
    if url and not already:
        # Log to sentiment_log_rss.csv
        log_sentiment("market", sentiment, page_source, log_date=pub_date.date())
        mark_processed(url, page_source, process_date=pub_date.date())
    # Append to results for display
    results.append({
        "title": title,
        "source": article_source,
        "publishedAt": pub_str,
        "summary": summary,
        "sentiment": sentiment
    })

# Filter by sentiment selection
filtered = [r for r in results if r["sentiment"] in selected_sentiments]

# Display articles
if not filtered:
    st.write("No articles match the selected filters.")
else:
    for r in filtered:
        st.markdown(f"### {r['title']}")
        st.caption(f"{r['source']} • {r['publishedAt']}")
        st.success(r['summary'])
        st.markdown(f"*Sentiment:* **{r['sentiment'].title()}**")
        st.markdown("---")

    # Show sentiment counts
    bullish_count = sum(1 for r in filtered if r['sentiment'] == 'bullish')
    neutral_count = sum(1 for r in filtered if r['sentiment'] == 'neutral')
    bearish_count = sum(1 for r in filtered if r['sentiment'] == 'bearish')
    col1, col2, col3 = st.columns(3)
    col1.metric("Bullish", bullish_count)
    col2.metric("Neutral", neutral_count)
    col3.metric("Bearish", bearish_count) 