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

KEYWORDS = ["陀螺", "比賽", "大賽", "報名", "G3"]
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
    message += f"🔔 **來源：{updated_store}**\n"
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

    for store, url in STORES.items():
        latest_posts = fetch_mobile_fb(url)
        if latest_posts:
            db[store] = latest_posts

    # 測試模式：直接強制發送目前的最新抓取結果到 Discord 讓你確認
    save_db(db)
    send_notification("手動檢查測試（各店最新狀態）", db)
    print("Test notification sent successfully.")

if __name__ == "__main__":
    main()
