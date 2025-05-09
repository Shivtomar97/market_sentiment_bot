import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
import os
from itertools import product

# Page config
st.set_page_config(layout="wide", page_title="Market Strategy Dashboard")
st.title("📊 Market Sentiment Dashboard")

# Add refresh button to clear the cache
if st.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()

# Sidebar filters
st.sidebar.header("Filters")

# Source selector
sources = ["NewsAPI", "RSS"]
selected_sources = st.sidebar.multiselect(
    "Select data sources", options=sources, default=sources
)

# Load and process sentiment data
@st.cache_data(ttl=60)  # Cache for 1 minute
def load_sentiment_data():
    dfs = []
    
    # Load NewsAPI data if available
    newsapi_path = "sentiment_log_newsapi.csv"
    if os.path.exists(newsapi_path) and os.path.getsize(newsapi_path) > 0:
        try:
            df_newsapi = pd.read_csv(newsapi_path, parse_dates=['date'])
            df_newsapi['source'] = 'NewsAPI'
            dfs.append(df_newsapi)
        except Exception as e:
            st.warning(f"Error reading NewsAPI data: {e}")
    
    # Load RSS data if available
    rss_path = "sentiment_log_rss.csv"
    if os.path.exists(rss_path) and os.path.getsize(rss_path) > 0:
        try:
            df_rss = pd.read_csv(rss_path, parse_dates=['date'])
            df_rss['source'] = 'RSS'
            dfs.append(df_rss)
        except Exception as e:
            st.warning(f"Error reading RSS data: {e}")
    
    # Combine data
    if not dfs:
        return pd.DataFrame(columns=['date', 'ticker', 'sentiment', 'source'])
    
    df_combined = pd.concat(dfs, ignore_index=True)
    return df_combined

# Load data
df = load_sentiment_data()

# Filter to last 7 days
cutoff_date = pd.Timestamp(date.today() - timedelta(days=7))
df = df[df['date'] >= cutoff_date]

# Get unique tickers
all_tickers = sorted(df['ticker'].unique().tolist())
if not all_tickers:
    st.warning("No ticker data available in the last 7 days.")
    st.stop()

# Ticker selector
selected_tickers = st.sidebar.multiselect(
    "Select tickers to display", options=all_tickers, default=all_tickers[:5] if len(all_tickers) > 5 else all_tickers
)

# Filter data based on selections
filtered_df = df[
    df['ticker'].isin(selected_tickers) & 
    df['source'].isin(selected_sources)
]

if filtered_df.empty:
    st.warning("No data available for the selected filters.")
    st.stop()

# Main dashboard content
st.header("Sentiment Distribution by Source and Ticker")

# Group data for visualization and ensure all combinations exist
# First, get all unique values
all_tickers = filtered_df['ticker'].unique()
all_sources = filtered_df['source'].unique()
all_sentiments = filtered_df['sentiment'].unique()

# Create empty DataFrame with MultiIndex to ensure all combinations
idx = pd.MultiIndex.from_product(
    [all_tickers, all_sources, all_sentiments], 
    names=['ticker', 'source', 'sentiment']
)
sentiment_counts = pd.Series(0, index=idx).reset_index(name='count')

# Fill in actual counts
actual_counts = filtered_df.groupby(['ticker', 'source', 'sentiment']).size().reset_index(name='count')

# Merge to keep all combinations but update with real counts
sentiment_counts = pd.merge(
    sentiment_counts, actual_counts, 
    on=['ticker', 'source', 'sentiment'],
    how='left', suffixes=('', '_actual')
)
# Use actual counts where available, keep zeros otherwise
sentiment_counts['count'] = sentiment_counts['count_actual'].fillna(0)
sentiment_counts = sentiment_counts.drop('count_actual', axis=1)

# Sentiment bar chart
fig = px.bar(
    sentiment_counts,
    x='ticker',
    y='count',
    color='sentiment',
    facet_col='source',
    barmode='group',
    hover_data=['ticker', 'sentiment', 'count', 'source'],
    color_discrete_map={
        'bullish': 'green',
        'neutral': 'gray',
        'bearish': 'red',
        'unknown': 'lightgray'
    },
    title="Sentiment Distribution by Source and Ticker (Last 7 Days)",
    labels={'count': 'Number of Articles', 'ticker': 'Ticker'},
    height=500
)
st.plotly_chart(fig, use_container_width=True)

# Summary metrics
st.header("Sentiment Summary by Ticker")

# Calculate and display summary metrics by ticker
ticker_summary = filtered_df.groupby(['ticker', 'sentiment']).size().unstack(fill_value=0)
ticker_summary = ticker_summary.reindex(columns=['bullish', 'neutral', 'bearish'], fill_value=0)

# Ticker metrics with pie charts
cols = st.columns(len(selected_tickers) if len(selected_tickers) <= 5 else 5)
for i, ticker in enumerate(selected_tickers[:5]):  # Limit to 5 tickers in the first row
    if ticker in ticker_summary.index:
        with cols[i % 5]:
            ticker_data = ticker_summary.loc[ticker]
            
            # Calculate totals
            total = ticker_data.sum()
            if total > 0:
                bullish_pct = f"{ticker_data.get('bullish', 0)/total:.0%}"
                bearish_pct = f"{ticker_data.get('bearish', 0)/total:.0%}"
                neutral_pct = f"{ticker_data.get('neutral', 0)/total:.0%}"
                
                # Pie chart
                fig = px.pie(
                    values=ticker_data,
                    names=ticker_data.index,
                    title=f"{ticker} Sentiment",
                    color=ticker_data.index,
                    color_discrete_map={
                        'bullish': 'green',
                        'neutral': 'gray',
                        'bearish': 'red'
                    }
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
                
                # Metrics
                st.metric("Bullish", bullish_pct)
                st.metric("Bearish", bearish_pct)

# Date range info
st.caption(f"Showing data from {cutoff_date.date()} to {date.today()}")

# Add historical trend
if st.checkbox("Show Historical Trend", value=False):
    st.subheader("Sentiment Trend Over Time")
    
    # Group by date and sentiment
    trend_df = filtered_df.groupby(['date', 'sentiment']).size().reset_index(name='count')
    
    # Create line chart
    fig = px.line(
        trend_df,
        x='date',
        y='count',
        color='sentiment',
        color_discrete_map={
            'bullish': 'green',
            'neutral': 'gray',
            'bearish': 'red',
            'unknown': 'lightgray'
        },
        title="Sentiment Trend Over Time",
        labels={'count': 'Number of Articles', 'date': 'Date'}
    )
    st.plotly_chart(fig, use_container_width=True) 