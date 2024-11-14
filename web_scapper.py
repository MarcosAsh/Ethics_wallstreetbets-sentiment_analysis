import praw
import pandas as pd
import re
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Set up Reddit API with PRAW
reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_SECRET"),
    username=os.getenv("REDDIT_USERNAME"),
    password=os.getenv("REDDIT_PASSWORD"),
    user_agent=os.getenv("USER_AGENT")
)


# Initialize sentiment analyzer
analyzer = SentimentIntensityAnalyzer()

# Stock ticker pattern (assuming uppercase tickers of 1-5 letters)
ticker_pattern = r'\b[A-Z]{1,5}\b'


# Scraper function
def scrape_wsb_posts(limit=100):
    posts_data = []
    for submission in reddit.subreddit('wallstreetbets').new(limit=limit):
        # Collect basic post data
        post = {
            'title': submission.title,
            'text': submission.selftext,
            'score': submission.score,
            'comments': submission.num_comments
        }

        # Extract possible stock tickers
        text_combined = post['title'] + " " + post['text']
        tickers = re.findall(ticker_pattern, text_combined)

        # Remove common words falsely identified as tickers
        exclude_list = {'YOLO', 'USA', 'THE'}  # Add more words as needed
        tickers = [ticker for ticker in tickers if ticker not in exclude_list]

        post['tickers'] = tickers

        # Perform sentiment analysis
        sentiment = analyzer.polarity_scores(text_combined)
        post['sentiment'] = sentiment['compound']

        posts_data.append(post)

    return pd.DataFrame(posts_data)


# Function to get top tickers and their average sentiment
def analyze_top_tickers(df):
    ticker_sentiments = {}
    for _, row in df.iterrows():
        for ticker in row['tickers']:
            if ticker not in ticker_sentiments:
                ticker_sentiments[ticker] = {'mentions': 0, 'total_sentiment': 0}
            ticker_sentiments[ticker]['mentions'] += 1
            ticker_sentiments[ticker]['total_sentiment'] += row['sentiment']

    # Create a dataframe of the results
    ticker_df = pd.DataFrame([
        {'ticker': ticker,
         'mentions': data['mentions'],
         'avg_sentiment': data['total_sentiment'] / data['mentions']}
        for ticker, data in ticker_sentiments.items()
    ])
    ticker_df = ticker_df.sort_values(by='mentions', ascending=False)

    return ticker_df


# Running the script
if __name__ == "__main__":
    # Scrape the posts
    posts_df = scrape_wsb_posts(limit=100)

    # Analyze the most mentioned tickers
    ticker_analysis_df = analyze_top_tickers(posts_df)

    # Save the analysis to a CSV file
    output_path = '/mnt/data/ticker_analysis.csv'
    ticker_analysis_df.to_csv(output_path, index=False)

    print(f"Ticker analysis saved to {output_path}")
    print(ticker_analysis_df.head(10))  # Display top 10 tickers and sentiment
