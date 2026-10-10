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

def fetch_mobile_fb(url):
    m_url = url.replace("www.facebook.com", "m.facebook.com")
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    try:
        res = requests.get(m_url, headers=headers, timeout=10)
        print(f"Fetching {m_url} - Status Code: {res.status_code}")
        if res.status_code != 200:
            return []
        
        soup = BeautifulSoup(res.text, 'html.parser')
        posts = []
        
        # 擴大搜尋範圍：抓取所有可能包含內文的 div 或 article
        elements = soup.find_all(['article', 'div'], class_=['story_body_container', '_5rgt', '_52jj'])
        if not elements:
            # 如果找不到特定 class，嘗試抓取所有文字段落較長的 div
            elements = soup.find_all('div', style=True) or soup.find_all('p')

        print(f"Found {len(elements)} potential blocks for {url}")

        for el in elements:
            text = el.get_text().strip()
            if len(text) < 10:  # 排除太短的無效字串
                continue
            
            lower_text = text.lower()
            if any(kw in lower_text for kw in KEYWORDS):
                posts.append({
                    "content": text[:150].strip() + "...",
                    "full_text": text.strip()
                })
            if len(posts) == 3:
                break
        
        # 如果透過結構找不到，嘗試把整個網頁文字抓出來作關鍵字比對備用
        if not posts:
            body_text = soup.get_text()
            if any(kw in body_text.lower() for kw in KEYWORDS):
                posts.append({
                    "content": "偵測到頁面包含關鍵字，但無法精確切割單篇貼文...",
                    "full_text": "請直接點擊粉專連結查看詳細內容。"
                })

        return posts
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return []

def send_notification(updated_store, all_data):
    if not WEBHOOK_URL:
        print("Webhook URL not set!")
        return

    message = f"🚨 **【陀螺 / G3 賽事最新動態檢查】** 🚨\n"
    message += f"🔔 **狀態：{updated_store}**\n"
    message += "==============================\n\n"

    for store, posts in all_data.items():
        message += f"🏪 **【{store}】**\n"
        if not posts:
            message += "  目前無相關「陀螺」或妹妹「G3」貼文\n\n"
        else:
            for idx, post in enumerate(posts, 1):
                message += f"  [{idx}] {post['content']}\n"
                message += f"      📌 內文摘要：{post['full_text'][:100]}...\n\n"
        message += "------------------------------\n"

    requests.post(WEBHOOK_URL, json={"content": message})

def main():
    db = load_db()

    for store, url in STORES.items():
        latest_posts = fetch_mobile_fb(url)
        if latest_posts:
            db[store] = latest_posts

    save_db(db)
    send_notification("網頁解析調整測試", db)
    print("Test notification sent successfully.")

if __name__ == "__main__":
    main()
