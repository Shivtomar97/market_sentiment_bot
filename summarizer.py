import os
import openai
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def summarize(text, ticker):
    prompt = (
        f"You are analyzing a stock market news summary for the ticker {ticker}.\n"
        "Your task is to classify the overall sentiment as one of the following:\n"
        "- Bullish (if the article suggests a positive outlook or upside)\n"
        "- Bearish (if it suggests risks, decline, or negative outcomes)\n"
        "- Neutral (if no clear direction is implied or it's too speculative)\n\n"
        "Avoid inferring sentiment unless there is clear evidence.\n"
        "If the article is too vague or mixed, choose Neutral.\n\n"
        "Respond in this exact format:\n"
        "Sentiment: <Bullish | Bearish | Neutral>\n"
        "Suggested Action: <a short recommendation to investors>\n\n"
        f"News Summary:\n{text}"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error summarizing: {e}"
