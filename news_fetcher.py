from dotenv import load_dotenv
load_dotenv()
import requests
import os
import yfinance as yf
from urllib.parse import quote_plus

def get_news(ticker):
    API_KEY = os.getenv("NEWS_API_KEY", "")
    # Build search query combining ticker and company name for broader relevance
    try:
        info = yf.Ticker(ticker).info
        company_name = info.get("longName") or info.get("shortName") or ""
    except Exception:
        company_name = ""
    # Only add company name if it's different than the ticker
    query = f"{ticker}"
    if company_name and company_name.upper() != ticker.upper():
        query += f' OR "{company_name}"'
    # URL-encode the query
    encoded_query = quote_plus(query)
    url = f"https://newsapi.org/v2/everything?q={encoded_query}&apiKey={API_KEY}&pageSize=6"
    
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
    return articles
