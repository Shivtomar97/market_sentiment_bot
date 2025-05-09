from dotenv import load_dotenv
load_dotenv()
import requests
import os
from datetime import date, timedelta, datetime
from urllib.parse import quote_plus
import re
import feedparser

def get_news(ticker):
    API_KEY = os.getenv("NEWS_API_KEY", "")
    # Restrict news to the past 7 days
    start_date = (date.today() - timedelta(days=7)).isoformat()
    # Build search query combining ticker and company name for broader relevance
    try:
        info = yf.Ticker(ticker).info
        company_name = info.get("longName") or info.get("shortName") or ""
    except Exception:
        company_name = ""
    # Only add company name if it's different than the ticker
    # Restrict search to the ticker followed by 'stock' to reduce irrelevant results
    query = f'"{ticker} stock"'
    if company_name and company_name.upper() != ticker.upper():
        query += f' OR "{company_name}"'
    # URL-encode the query
    encoded_query = quote_plus(query)
    url = (
        f"https://newsapi.org/v2/everything?q={encoded_query}"
        f"&apiKey={API_KEY}"
        f"&from={start_date}"  # last 7 days
        f"&sortBy=publishedAt&language=en"
        f"&pageSize=6&excludeDomains=yahoo.com"
    )
    
    response = requests.get(url)
    print("DEBUG: NewsAPI response code:", response.status_code)
    print("DEBUG: NewsAPI response:", response.text)

    if response.status_code != 200:
        return []
    
    data = response.json()
    articles = []
    for item in data.get("articles", []):
        articles.append({
            "title": item["title"],
            "url": item["url"],
            "description": item["description"],
            "publishedAt": item["publishedAt"],
            "source": item["source"]["name"]
        })
    # Compile regex for exact ticker/company name matches
    pattern_parts = [re.escape(ticker)]
    if company_name:
        pattern_parts.append(re.escape(company_name))
    pattern = r"\b(?:" + "|".join(pattern_parts) + r")\b"
    regex = re.compile(pattern, re.IGNORECASE)
    # Filter to only articles matching full-word ticker or company name
    relevant = []
    for art in articles:
        text = (art.get('title', '') + ' ' + (art.get('description') or ''))
        if regex.search(text):
            relevant.append(art)
    return relevant

def get_general_news():
    """
    Fetch general stock market news for the past 7 days using a broad query.
    """
    API_KEY = os.getenv("NEWS_API_KEY", "")
    # Fetch news from the last 7 days
    start_date = (date.today() - timedelta(days=7)).isoformat()
    # Broad market news query
    query = "stock market OR S&P OR earnings OR investors OR markets"
    encoded_query = quote_plus(query)
    url = (
        f"https://newsapi.org/v2/everything?q={encoded_query}"
        f"&apiKey={API_KEY}"
        f"&from={start_date}"  # last 7 days
        f"&sortBy=publishedAt&language=en"
        f"&pageSize=6&excludeDomains=yahoo.com"
    )
    response = requests.get(url)
    if response.status_code != 200:
        return []
    data = response.json()
    articles = []
    for item in data.get("articles", []):
        articles.append({
            "title": item.get("title"),
            "url": item.get("url"),
            "description": item.get("description"),
            "publishedAt": item.get("publishedAt"),
            "source": item.get("source", {}).get("name")
        })
    return articles

def get_rss_news(ticker):
    """
    Fetch headlines via Yahoo Finance RSS for the given ticker.
    """
    feed = feedparser.parse(
        f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"
    )
    articles = []
    # Only include articles from the last 7 days
    cutoff = datetime.utcnow() - timedelta(days=7)
    for entry in feed.entries:
        parsed = entry.get("published_parsed")
        if not parsed:
            continue
        dt = datetime(*parsed[:6])
        # Exclude articles older than 7 days
        if dt < cutoff:
            continue
        # Use the RSS summary as the description for GPT summarization
        desc = entry.get("summary") or entry.get("description") or ""
        articles.append({
            "title": entry.get("title"),
            "url": entry.get("link"),
            "description": desc,
            "publishedAt": dt.isoformat(),
            "source": "Yahoo Finance RSS"
        })
    # Return only the first 10 relevant articles
    return articles[:10]

import feedparser
from datetime import datetime, timedelta

import feedparser
from datetime import datetime, timedelta

def get_rss_general_news():
    """
    Fetch general stock market news from Yahoo Finance RSS (^GSPC) for the past 7 days.
    """
    url_feed = "https://feeds.finance.yahoo.com/rss/2.0/headline?s=%5EDJI&region=US&lang=en-US"
    feed = feedparser.parse(url_feed)
    articles = []
    cutoff = datetime.utcnow() - timedelta(days=7)

    for entry in feed.entries:
        parsed = entry.get("published_parsed")
        if not parsed:
            continue
        dt = datetime(*parsed[:6])
        if dt < cutoff:
            continue
        desc = entry.get("summary") or entry.get("description") or ""
        articles.append({
            "title": entry.get("title"),
            "url": entry.get("link"),
            "description": desc,
            "publishedAt": dt.isoformat(),
            "source": "Yahoo Finance (^GSPC)"
        })

    return articles[:10]
