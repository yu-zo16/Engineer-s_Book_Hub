import requests
import re
import time
from datetime import datetime, timedelta
from supabase import create_client

# --- 設定 ---
SUPABASE_URL = "https://dndowbpxacdncjsoqmlh.supabase.co"
SUPABASE_KEY = "sb_publishable_tc2XxJANYH57uQHLapU2RQ_S1YmGztr"
QIITA_TOKEN = "0c66390d678730f59f6bd582d6596af5def1f618"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 1. 巡回する技術タグ（より細かく、網羅的に）
TARGET_TAGS = [
    "AWS", "Docker", "Kubernetes", "Terraform", "Linux", "Azure", "Ansible", "GCP", "Network", # インフラ
    "React", "TypeScript", "Next.js", "Vue", "TailwindCSS", "JavaScript",            # フロント
    "Python", "Go", "Rust", "Ruby", "Node.js", "Java", "PHP", "SQL",                # バック
    "Architecture", "設計", "DDD", "Git", "GitHub",                                  # 共通
    "技術書", "書籍", "読書"                                                          # 書籍関連直接
]

# 2. 検索の切り口を増やす（「書籍」以外のワードでも本は見つかるため）
SUB_QUERIES = ["書籍", "本", "おすすめ", "紹介"]

def get_asin(url):
    """URLからASIN(10桁の商品コード)を抽出"""
    asin_match = re.search(r"/(?:dp|gp/product|gp/aw/d)/([A-Z0-9]{10})", url)
    if asin_match:
        return asin_match.group(1)
    return None

def collect_step1_qiita_strict():
    # 365日前からのデータを取得対象にする
    since_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    print(f"🚀 【大量収集モード】開始: {since_date} 以降の記事を多角的にスキャンします。")

    processed_urls = set() # 1回の実行中での重複処理を防止

    for tag in TARGET_TAGS:
        for sub in SUB_QUERIES:
            print(f"\n--- 🔎 検索: tag:{tag} + {sub} ---")
            query = f"tag:{tag} {sub}"
            
            for page in range(1, 4): # 各クエリ最大3ページ(300件)チェック
                headers = {"Authorization": f"Bearer {QIITA_TOKEN}"}
                url = f"https://qiita.com/api/v2/items?page={page}&per_page=100&query={query} created:>{since_date}"
                
                try:
                    res = requests.get(url, headers=headers)
                    if res.status_code == 429:
                        print("⚠️ API制限中... 60秒待機します")
                        time.sleep(60)
                        continue
                    elif res.status_code != 200:
                        break
                    
                    items = res.json()
                    if not items: break

                    for item in items:
                        if item['url'] in processed_urls: continue
                        
                        title = item['title']
                        # タグの厳格チェック（直接「技術書」などのタグ検索時はスルーしてOK）
                        actual_tags = [t['name'].lower() for t in item['tags']]
                        if tag.lower() not in ["技術書", "書籍", "読書"] and tag.lower() not in actual_tags:
                            continue

                        # Amazonリンクの抽出
                        links = re.findall(r'https?://(?:www\.)?amazon\.co\.jp/[^\s)]+|https?://amzn\.to/[a-zA-Z0-9]+', item['body'])
                        if not links:
                            continue

                        article_data = {
                            "title": title,
                            "url": item['url'],
                            "body": item['body'][:500],
                            "likes_count": item['likes_count'],
                            "tags": [t['name'] for t in item['tags']], 
                            "published_at": item['created_at']
                        }
                        
                        try:
                            stored = supabase.table("articles").upsert(article_data, on_conflict="url").execute()
                            if stored.data:
                                article_id = stored.data[0]['id']
                                processed_urls.add(item['url'])
                                
                                for link in set(links):
                                    asin = get_asin(link)
                                    book_data = {
                                        "article_id": article_id,
                                        "title": "Pending...",
                                        "raw_link": link,
                                        "asin": asin,
                                        "status": "pending"
                                    }
                                    supabase.table("books").insert(book_data).execute()
                                
                                print(f"  ✨ [採用] {title[:20]}... (Tag:{tag})")

                        except Exception:
                            continue

                    time.sleep(1.0) # 負荷軽減

                except Exception as e:
                    print(f"  [Error] {tag}のスキャン中に問題発生: {e}")
                    break

if __name__ == "__main__":
    collect_step1_qiita_strict()