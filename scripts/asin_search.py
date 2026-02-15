import requests
import re
import time
from supabase import create_client

# --- 設定（必ず前回のスクリプトと一致させてください） ---
SUPABASE_URL = "https://dndowbpxacdncjsoqmlh.supabase.co"
SUPABASE_KEY = "sb_publishable_tc2XxJANYH57uQHLapU2RQ_S1YmGztr"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def extract_asin_precision(url):
    """
    短縮URLを展開し、正規表現で10桁のASINを抜き出す
    """
    final_url = url
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
    }
    
    # 1. 短縮URLの展開（amzn.to, amzn.asia, bit.ly など）
    if any(domain in url for domain in ["amzn.to", "amzn.asia", "bit.ly", "t.co"]):
        try:
            # HEADリクエストでリダイレクト先だけを高速に取得
            res = requests.get(url, timeout=10, headers=headers, allow_redirects=True)
            final_url = res.url
        except Exception as e:
            print(f"    ⚠️ 展開失敗: {url} -> {e}")

    # 2. ASIN抽出（正規表現パターン）
    patterns = [
        r'/dp/([A-Z0-9]{10})',
        r'/gp/product/([A-Z0-9]{10})',
        r'/gp/aw/d/([A-Z0-9]{10})',
        r'/ASIN/([A-Z0-9]{10})',
        r'amazon\.co\.jp/([A-Z0-9]{10})'
    ]
    
    for p in patterns:
        match = re.search(p, final_url)
        if match:
            return match.group(1)
            
    return None

def run_step1_asin_fill():
    print("🚀 Step 1: 超精密ASIN特定モードを開始します...")
    
    # ASINが未登録（null）のものを取得
    # 注意: statusが'pending'のものだけを対象にすると効率的です
    try:
        res = supabase.table("books").select("id, raw_link").is_("asin", "null").execute()
        books = res.data
    except Exception as e:
        print(f"❌ DB接続エラー: {e}")
        return

    if not books:
        print("✅ 全てのデータのASIN特定が完了しているか、対象データがありません。")
        return

    print(f"📊 処理対象: {len(books)} 件")

    

    for b in books:
        raw_link = b['raw_link']
        # 稀にリンク自体に不備がある場合をガード
        if not raw_link: continue

        asin = extract_asin_precision(raw_link)
        
        if asin:
            try:
                supabase.table("books").update({"asin": asin}).eq("id", b['id']).execute()
                print(f"  ✅ 特定成功: {asin}")
            except Exception as e:
                print(f"  ❌ DB更新失敗: {e}")
        else:
            print(f"  ❌ 特定不能: {raw_link[:50]}...")
        
        # Amazonへの連続アクセスによるBANを防ぐため、少し長めに待機
        time.sleep(1.2)

if __name__ == "__main__":
    run_step1_asin_fill()