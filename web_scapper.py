import praw
import pandas as pd
import re
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
def scrape_wsb_posts_with_comments(limit=100):
    posts_data = []
    for submission in reddit.subreddit('wallstreetbets').new(limit=limit):
        # Collect basic post data
        post = {
            'title': submission.title,
            'text': submission.selftext,
            'score': submission.score,
            'comments': []
        }

        # Extract possible stock tickers
        text_combined = post['title'] + " " + post['text']
        tickers = re.findall(ticker_pattern, text_combined)

        # Remove common words falsely identified as tickers
        exclude_list = {'YOLO', 'USA', 'THE'}  # Add more words as needed
        tickers = [ticker for ticker in tickers if ticker not in exclude_list]

        post['tickers'] = tickers

        # Perform sentiment analysis for the post
        sentiment = analyzer.polarity_scores(text_combined)
        post['post_sentiment'] = sentiment['compound']
        post['post_sentiment_category'] = 'Bullish' if sentiment['compound'] > 0 else 'Bearish'

        # Fetch and analyze comments
        submission.comments.replace_more(limit=0)
        for comment in submission.comments.list():
            if comment.body:  # Ensure comment is not empty
                comment_sentiment = analyzer.polarity_scores(comment.body)
                sentiment_category = 'Bullish' if comment_sentiment['compound'] > 0 else 'Bearish'

                post['comments'].append({
                    'comment_text': comment.body,
                    'comment_sentiment': comment_sentiment['compound'],
                    'sentiment_category': sentiment_category
                })

        posts_data.append(post)

    return posts_data


# Analyze ticker mentions and sentiment
def analyze_top_tickers(posts_data):
    ticker_sentiments = {}
    for post in posts_data:
        for ticker in post['tickers']:
            if ticker not in ticker_sentiments:
                ticker_sentiments[ticker] = {'mentions': 0, 'total_sentiment': 0}
            ticker_sentiments[ticker]['mentions'] += 1
            ticker_sentiments[ticker]['total_sentiment'] += post['post_sentiment']

    # Create a dataframe of the results
    ticker_df = pd.DataFrame([
        {'ticker': ticker,
         'mentions': data['mentions'],
         'avg_sentiment': data['total_sentiment'] / data['mentions']}
        for ticker, data in ticker_sentiments.items()
    ])
    ticker_df = ticker_df.sort_values(by='mentions', ascending=False)

    return ticker_df


# Save posts and analysis to CSV
def save_to_csv(posts_data, ticker_analysis_df):
    # Save detailed posts data
    posts_flattened = []
    for post in posts_data:
        for comment in post['comments']:
            posts_flattened.append({
                'title': post['title'],
                'post_sentiment': post['post_sentiment'],
                'post_sentiment_category': post['post_sentiment_category'],
                'ticker_mentions': ', '.join(post['tickers']),
                'comment_text': comment['comment_text'],
                'comment_sentiment': comment['comment_sentiment'],
                'comment_sentiment_category': comment['sentiment_category']
            })

    posts_df = pd.DataFrame(posts_flattened)
    posts_df.to_csv('wsb_posts_with_comments.csv', index=False)

    # Save ticker analysis
    ticker_analysis_df.to_csv('ticker_analysis.csv', index=False)


# Running the script
if __name__ == "__main__":
    # Scrape the posts and their comments
    posts_data = scrape_wsb_posts_with_comments(limit=100)

    # Analyze the most mentioned tickers
    ticker_analysis_df = analyze_top_tickers(posts_data)

    # Save the data to CSV files
    save_to_csv(posts_data, ticker_analysis_df)

    print("Data saved to 'wsb_posts_with_comments.csv' and 'ticker_analysis.csv'")
    print(ticker_analysis_df.head(10))  # Display top 10 tickers and sentiment
