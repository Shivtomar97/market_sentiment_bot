import os
import openai
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def summarize(text, ticker):
    prompt = f"""
You are a financial assistant. Based on this news about {ticker}, return exactly two lines:
1. Sentiment: Bullish, Bearish, or Neutral — based on how the news is likely to affect the stock price.
2. Suggested Action: A one-line investor recommendation (e.g., Buy, Hold, Monitor, Reduce Exposure, etc.)

Format:
Sentiment: <Bullish/Bearish/Neutral>.
Suggested Action: <your sentence here>.

News Article:
\"\"\"
{text}
\"\"\"
"""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error summarizing: {e}"
