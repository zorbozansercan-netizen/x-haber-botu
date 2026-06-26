import os
import time
import json
import feedparser
import tweepy
import google.generativeai as genai

# 1. Şifreleri Güvenli Kasadan Çekme
X_API_KEY = os.environ["X_API_KEY"]
X_API_KEY_SECRET = os.environ["X_API_KEY_SECRET"]
X_ACCESS_TOKEN = os.environ["X_ACCESS_TOKEN"]
X_ACCESS_TOKEN_SECRET = os.environ["X_ACCESS_TOKEN_SECRET"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

# 2. Bağlantıları Başlatma (X ve Gemini)
client = tweepy.Client(
    consumer_key=X_API_KEY, consumer_secret=X_API_KEY_SECRET,
    access_token=X_ACCESS_TOKEN, access_token_secret=X_ACCESS_TOKEN_SECRET
)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Takip edilecek küresel haber kaynakları (RSS)
RSS_FEEDS = [
    "http://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.reutersagency.com/feed/?best-topics=political-general"
]

DATA_FILE = "posted_news.json"

def load_posted_news():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []

def save_posted_news(posted_list):
    with open(DATA_FILE, "w") as f:
        json.dump(posted_list, f)

def rewrite_with_gemini(title, summary):
    prompt = f"You are a professional, elite global military and political intelligence news platform on X (like clashreport). Translate and rewrite the following news title and summary into English. Use direct, fluent, expert, and journalistic language. Keep it very short, punchy, and concise. CRITICAL: Never use hyphens (-) or emojis. Go straight to the point.\n\nTitle: {title}\nSummary: {summary}"
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Gemini hatası: {e}")
        return None

def main():
    posted_news = load_posted_news()
    new_posts = []
    
    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:5]: # Son 5 haberi kontrol et
            news_id = entry.get("id", entry.link)
            if news_id in posted_news:
                continue
                
            title = entry.title
            summary = entry.get("summary", "")
            
            print(f"Yeni haber bulundu: {title}")
            tweet_text = rewrite_with_gemini(title, summary)
            
            if tweet_text:
                if len(tweet_text) > 275:
                    tweet_text = tweet_text[:272] + "..."
                try:
                    client.create_tweet(text=tweet_text)
                    print(f"Tweet atıldı: {tweet_text}")
                    new_posts.append(news_id)
                    time.sleep(5) # X kuralları için bekleme
                except Exception as e:
                    print(f"X Tweet atma hatası: {e}")
                    
    posted_news.extend(new_posts)
    save_posted_news(posted_news[-100:]) # Son 100 haberi hafızada tut

if __name__ == "__main__":
    main()
