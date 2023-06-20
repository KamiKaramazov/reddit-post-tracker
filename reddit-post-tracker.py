import requests
import time
import sqlite3
from flask import Flask, jsonify
from dotenv import load_dotenv
import os

app = Flask(__name__)

# .env dosyasını yükleyin
load_dotenv()

# SQLite veritabanı bağlantısı oluşturma
conn = sqlite3.connect('reddit_posts.db')
c = conn.cursor()

# Veritabanı tablosunu oluşturma
c.execute('''CREATE TABLE IF NOT EXISTS posts
             (id TEXT, title TEXT, subreddit TEXT)''')

# Reddit API ayarları
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
USERNAME = os.getenv('USERNAME')
PASSWORD = os.getenv('PASSWORD')

def login():
    """
    Reddit API'ına giriş yapmak için kullanıcı kimlik bilgileriyle oturum açar ve erişim token'ını döndürür.
    """
    url = 'https://www.reddit.com/api/v1/access_token'
    headers = {'User-Agent': 'My Reddit Bot'}
    data = {
        'grant_type': 'password',
        'username': USERNAME,
        'password': PASSWORD
    }
    response = requests.post(url, headers=headers, data=data, auth=(CLIENT_ID, CLIENT_SECRET))
    if response.status_code == 200:
        access_token = response.json()['access_token']
        return access_token
    else:
        raise Exception('Login failed. Check your credentials.')

def store_posts(posts):
    """
    Crawl edilen postları database'de saklar.
    """
    for post in posts:
        post_id = post['id']
        title = post['title']
        subreddit = post['subreddit']
        c.execute("INSERT INTO posts VALUES (?, ?, ?)", (post_id, title, subreddit))
    conn.commit()

def track_posts():
    """
    Reddit API'ından postları çeker ve takip eder.
    """
    access_token = login()
    headers = {'User-Agent': 'My Reddit Bot', 'Authorization': f'Bearer {access_token}'}
    url = 'https://oauth.reddit.com/r/python/new'
    while True:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()['data']['children']
            posts = []
            for post in data:
                post_data = post['data']
                posts.append({'id': post_data['id'], 'title': post_data['title'], 'subreddit': post_data['subreddit']})
            store_posts(posts)
        else:
            print(f"Failed to fetch posts. Status Code: {response.status_code}")
        time.sleep(10)

# API endpoint'i
@app.route('/posts', methods=['GET'])
def get_all_posts():
    c.execute("SELECT * FROM posts")
    data = c.fetchall()
    posts = []
    for row in data:
        post = {
            'id': row[0],
            'title': row[1],
            'subreddit': row[2]
        }
        posts.append(post)
    return jsonify(posts)

if __name__ == '__main__':
    track_posts()
    app.run()
