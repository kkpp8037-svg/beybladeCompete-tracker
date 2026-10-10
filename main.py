import os
import json
import time
import requests
from bs4 import BeautifulSoup

STORES = {
    "聯萌玩具百貨精品批發": "https://www.facebook.com/lemon600/",
    "湯姆熊歡樂世界-台南海佃店": "https://www.facebook.com/TOMSWORLDSHD/",
    "翻轉x點子 桌遊館": "https://www.facebook.com/filpidea/",
    "玖零玩具": "https://www.facebook.com/100084424252105/",
    "扭蛋將軍x轉蛋概念館": "https://www.facebook.com/macross50711/"
}

KEYWORDS = ["陀螺", "比賽", "大賽", "報名"]
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

def fetch_mobile_fb(url):
    m_url = url.replace("www.facebook.com", "m.facebook.com")
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
    }
    try:
        res = requests.get(m_url, headers=headers, timeout=10)
        if res.status_code != 200:
            return []
        
        soup = BeautifulSoup(res.text, 'html.parser')
        posts = []
        
        for article in soup.find_all('article'):
            text = article.get_text()
            if any(kw in text for kw in KEYWORDS):
                posts.append({
                    "content": text[:150].strip() + "...",
                    "full_text": text.strip()
                })
            if len(posts) == 3:
                break
        return posts
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return []

def send_notification(updated_store, all_data):
    if not WEBHOOK_URL:
        print("Webhook URL not set!")
        return

    message = f"🚨 **【陀螺比賽最新動態通知】** 🚨\n"
    message += f"🔔 **更新來源：{updated_store}** 有新賽事資訊發布！\n"
    message += "==============================\n\n"

    for store, posts in all_data.items():
        message += f"🏪 **【{store}】（最新相關貼文）**\n"
        if not posts:
            message += "  目前無相關陀螺比賽貼文\n\n"
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

    for store, url in STORES.items():
        latest_posts = fetch_mobile_fb(url)
        if not latest_posts:
            continue
            
        old_first = db[store][0]['content'] if db.get(store) and len(db[store]) > 0 else ""
        new_first = latest_posts[0]['content'] if len(latest_posts) > 0 else ""

        # 只要第一篇貼文內容跟之前不一樣，就代表有新貼文
        if new_first and new_first != old_first:
            has_update = True
            updated_store_name = store

        db[store] = latest_posts

    # 只有當偵測到有新貼文時，才儲存並發送通知
    if has_update:
        save_db(db)
        send_notification(updated_store_name, db)
        print(f"Update detected from {updated_store_name}, notification sent.")
    else:
        print("No new updates found. Staying quiet.")

if __name__ == "__main__":
    main()
