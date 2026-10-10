import os
import json
import feedparser
import requests

# 💡 請將下方的網址換成你在 FetchRSS 產生的專屬 RSS 網址
STORES = {
    "聯萌玩具百貨精品批發": "https://fetchrss.com/feed/1xFWgyGhwFOc1xFWhR5nRFbm.rss",
    "湯姆熊歡樂世界-台南海佃店": "https://fetchrss.com/feed/1xFWgyGhwFOc1xFWmX81O0Ti.rss",
    "翻轉x點子 桌遊館": "https://fetchrss.com/feed/1xFWgyGhwFOc1xFWnBENu7XO.rss",
    "玖零玩具": "https://fetchrss.com/feed/1xFWgyGhwFOc1xFWnm1XQA30.rss",
    "扭蛋將軍x轉蛋概念館": "https://fetchrss.com/feed/1xFWgyGhwFOc1xFWoGFw40WI.rss"
}

KEYWORDS = ["陀螺", "g3"]
DB_FILE = "posts_db.json"
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {store: [] for store in STORES}

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def fetch_rss_posts(rss_url):
    """透過 RSS 讀取粉專貼文，穩定且不會被 FB 阻擋"""
    if "你的_FetchRSS網址" in rss_url:
        print("請先替換成真實的 RSS 網址！")
        return []
    
    try:
        feed = feedparser.parse(rss_url)
        posts = []
        
        for entry in feed.entries:
            title = getattr(entry, 'title', '')
            summary = getattr(entry, 'summary', '')
            full_text = f"{title}\n{summary}"
            
            lower_text = full_text.lower()
            if any(kw in lower_text for kw in KEYWORDS):
                posts.append({
                    "content": full_text[:150].strip() + "...",
                    "full_text": full_text.strip()
                })
            if len(posts) == 3:
                break
        return posts
    except Exception as e:
        print(f"Error parsing RSS {rss_url}: {e}")
        return []

def send_notification(updated_store, all_data):
    if not WEBHOOK_URL:
        print("Webhook URL not set!")
        return

    message = f"🚨 **【陀螺 / G3 賽事最新動態】** 🚨\n"
    message += f"🔔 **更新來源：{updated_store}** 有新賽事資訊發布！\n"
    message += "==============================\n\n"

    for store, posts in all_data.items():
        message += f"🏪 **【{store}】（最新相關貼文）**\n"
        if not posts:
            message += "  目前無相關「陀螺」或「G3」貼文\n\n"
        else:
            for idx, post in enumerate(posts, 1):
                message += f"  [{idx}] {post['content']}\n"
                message += f"      📌 內文摘要/報名提示：{post['full_text'][:100]}...\n\n"
        message += "------------------------------\n"

    requests.post(WEBHOOK_URL, json={"content": message})

def main():
    db = load_db()
    has_update = False
    updated_store_name = ""

    for store, rss_url in STORES.items():
        latest_posts = fetch_rss_posts(rss_url)
        if not latest_posts:
            continue
            
        old_first = db[store][0]['content'] if db.get(store) and len(db[store]) > 0 else ""
        new_first = latest_posts[0]['content'] if len(latest_posts) > 0 else ""

        # 比對第一篇貼文是否與資料庫不同
        if new_first and new_first != old_first:
            has_update = True
            updated_store_name = store

        db[store] = latest_posts

    # 只有當偵測到有新貼文時才發送通知（正式上線模式）
    if has_update:
        save_db(db)
        send_notification(updated_store_name, db)
        print(f"Update detected from {updated_store_name}, notification sent.")
    else:
        print("No new updates found. Staying quiet.")

if __name__ == "__main__":
    main()
