import streamlit as st
from news_fetcher import get_news
from summarizer import summarize
from app import extract_sentiment_keyword

# Streamlit page configuration
st.set_page_config(page_title="Market News", layout="wide")
st.title("📰 General Market News")

# Sidebar filter for sentiment
st.sidebar.header("Filters")
sentiments = ["bullish", "neutral", "bearish"]
selected_sentiments = st.sidebar.multiselect(
    "Select sentiment to display", options=sentiments, default=sentiments
)

# Fetch today's market news
articles = get_news("market")
if not articles:
    st.write("No news articles found for market.")
    st.stop()

# Process and analyze each article
results = []
for article in articles:
    title = article.get("title", "No title")
    source = article.get("source", "Unknown source")
    publishedAt = article.get("publishedAt", "")
    description = article.get("description") or article.get("content") or ""
    summary = summarize(description, "market")
    sentiment = extract_sentiment_keyword(summary)
    results.append({
        "title": title,
        "source": source,
        "publishedAt": publishedAt,
        "summary": summary,
        "sentiment": sentiment,
    })

# Filter results by selected sentiment
filtered = [r for r in results if r["sentiment"] in selected_sentiments]

# Display filtered articles
if not filtered:
    st.write("No articles match the selected sentiment filter.")
else:
    for r in filtered:
        st.markdown(f"### {r['title']}")
        st.caption(f"{r['source']} • {r['publishedAt']}")
        st.markdown(r['summary'])
        st.markdown(f"*Sentiment:* **{r['sentiment'].title()}**")
        st.markdown("---")

# Show total sentiment counts
bullish_count = sum(1 for r in filtered if r['sentiment'] == 'bullish')
neutral_count = sum(1 for r in filtered if r['sentiment'] == 'neutral')
bearish_count = sum(1 for r in filtered if r['sentiment'] == 'bearish')
col1, col2, col3 = st.columns(3)
col1.metric("Bullish", bullish_count)
col2.metric("Neutral", neutral_count)
col3.metric("Bearish", bearish_count) 