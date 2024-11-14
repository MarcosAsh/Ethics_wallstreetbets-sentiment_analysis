import pandas as pd
import re
import matplotlib.pyplot as plt

# Load the dataset
file_path = '/mnt/data/Reddit_wsb_labelled.csv'
reddit_data = pd.read_csv(file_path)

# Ensure the 'text' column is a string and handle missing values
reddit_data['text'] = reddit_data['text'].fillna('').astype(str)

# Define a stock ticker pattern (case insensitive)
ticker_pattern = r'\b[a-zA-Z]{1,5}\b'

# Define known stock tickers
known_tickers = ['GME', 'AMC', 'BBBY', 'RKT', 'NVDA']

# Extract stock tickers from the text column
reddit_data['tickers'] = reddit_data['text'].apply(lambda x: re.findall(ticker_pattern, x))
reddit_data['tickers'] = reddit_data['tickers'].apply(lambda tickers: [t.upper() for t in tickers if t.upper() in known_tickers])

# Explode the dataframe to associate each row with individual tickers
reddit_data_exploded = reddit_data.explode('tickers')

# Remove rows without any identified tickers
reddit_data_exploded = reddit_data_exploded.dropna(subset=['tickers'])

# Calculate sentiment distribution for individual stocks
stock_sentiment_distribution = reddit_data_exploded.groupby(['tickers', 'sentiment']).size().unstack(fill_value=0)

# Display the sentiment distribution
def plot_sentiment_distribution(stock_sentiment_distribution):
    for stock in stock_sentiment_distribution.index:
        stock_data = stock_sentiment_distribution.loc[stock]
        stock_data.plot(kind='bar', color=['salmon', 'gray', 'skyblue'], alpha=0.7, figsize=(8, 6))
        plt.title(f'Sentiment Distribution for {stock}')
        plt.xlabel('Sentiment (-1 = Bearish, 0 = Neutral, 1 = Bullish)')
        plt.ylabel('Number of Comments')
        plt.xticks(ticks=[0, 1, 2], labels=['Bearish', 'Neutral', 'Bullish'], rotation=0)
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.show()

# Plot the sentiment distribution
plot_sentiment_distribution(stock_sentiment_distribution)

# Calculate the frequency of stock mentions
stock_mentions = reddit_data_exploded['tickers'].value_counts()

# Plot the frequency of stock mentions
plt.figure(figsize=(10, 6))
stock_mentions.plot(kind='bar', color='skyblue', alpha=0.7)
plt.title('Frequency of Stock Mentions')
plt.xlabel('Stock Ticker')
plt.ylabel('Number of Mentions')
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.show()

# Save the sentiment distribution to a CSV file
output_path = '/mnt/data/stock_sentiment_distribution.csv'
stock_sentiment_distribution.to_csv(output_path)
print(f"Sentiment distribution saved to {output_path}")
