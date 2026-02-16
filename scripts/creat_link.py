import urllib.parse
import time
import re
import requests
from amazon.paapi import AmazonApi
from supabase import create_client

# --- 1. 設定情報 ---
# 現在使用中のSupabase情報に書き換えてください
SUPABASE_URL = "https://dndowbpxacdncjsoqmlh.supabase.co"
SUPABASE_KEY = "sb_publishable_tc2XxJANYH57uQHLapU2RQ_S1YmGztr"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Amazon API設定
AMZ_ACCESS_KEY = "AKPA46MKWR1768915366"
AMZ_SECRET_KEY = "qRA6+RsuAZ6w9H6/8cMSUdicsz+Jp7hb7h4ZsCqT"
AMZ_ASSOCIATE_TAG = "yuzo0a-22"

# APIクライアントの初期化
amazon = AmazonApi(
    key=AMZ_ACCESS_KEY, 
    secret=AMZ_SECRET_KEY, 
    tag=AMZ_ASSOCIATE_TAG, 
    country="JP", 
    throttling=2.0 
)

def extract_asin_precision(url):
    """
    短縮URLの展開と、数字10桁を含むASINの超精密抽出
    """
    final_url = url
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    # 1. 短縮URLの展開
    if any(domain in url for domain in ["amzn.to", "amzn.asia", "bit.ly"]):
        try:
            res = requests.get(url, timeout=10, headers=headers, allow_redirects=True)
            final_url = res.url
        except:
            pass

    # 2. ASIN抽出ロジック（数字10桁とB0...の両方に対応）
    patterns = [
        r'/dp/([A-Z0-9]{10})',
        r'/gp/product/([A-Z0-9]{10})',
        r'/gp/aw/d/([A-Z0-9]{10})',
        r'[/=]([A-Z0-9]{10})(?:[?&/]|#|$)' # URLの末尾やパラメータを拾う
    ]
    
    for p in patterns:
        match = re.search(p, final_url)
        if match:
            return match.group(1)
    return None

def enrich_books_data():
    print("🚀 Amazonデータ補完フェーズ開始（数字ASIN対応版）")

    # ASINが未取得、またはstatusがcompleted以外のデータを取得
    res = supabase.table("books").select("*").neq("status", "completed").execute()
    target_books = res.data

    if not target_books:
        print("✅ 更新が必要なデータはありません。")
        return

    print(f"📊 処理対象: {len(target_books)} 件")

    for book in target_books:
        book_id = book['id']
        raw_link = book['raw_link']
        asin = book.get('asin')

        # もしASINが空なら、この場でもう一度抽出を試みる
        if not asin or len(asin) != 10:
            asin = extract_asin_precision(raw_link)
        
        if not asin:
            print(f"  ❌ ASIN特定不能: {raw_link[:40]}")
            continue

        print(f"🔍 API照会中: {asin}")

        try:
            # Amazon PA-APIにリクエスト
            results = amazon.get_items(items=[asin])
            
            if results and len(results) > 0:
                item = results[0]
                
                # 情報の抽出
                formal_title = item.item_info.title.display_value
                
                # 画像URL（Lサイズ）
                image_url = None
                if item.images and item.images.primary and item.images.primary.large:
                    image_url = item.images.primary.large.url
                
                # アフィリエイトリンク（検索結果ページへ飛ばすことで成約率UP）
                encoded_title = urllib.parse.quote(formal_title)
                affiliate_search_url = f"https://www.amazon.co.jp/s?k={encoded_title}&i=stripbooks&tag={AMZ_ASSOCIATE_TAG}"

                # Supabase更新
                update_payload = {
                    "asin": asin,
                    "title": formal_title,
                    "amazon_url": affiliate_search_url,
                    "status": "completed"
                }
                if image_url:
                    update_payload["image_url"] = image_url

                supabase.table("books").update(update_payload).eq("id", book_id).execute()
                print(f"  ✅ 更新成功: {formal_title[:25]}")

            else:
                print(f"  ⚠️ 商品なし: {asin}")
                supabase.table("books").update({"status": "not_found", "asin": asin}).eq("id", book_id).execute()

            time.sleep(2) # 負荷軽減

        except Exception as e:
            print(f"  ❌ エラー (ASIN:{asin}): {e}")
            time.sleep(5)
            continue

if __name__ == "__main__":
    enrich_books_data()