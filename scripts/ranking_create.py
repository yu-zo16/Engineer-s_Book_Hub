import math
from datetime import datetime, date, timedelta
from supabase import create_client

# --- 設定 ---
SUPABASE_URL = "https://dndowbpxacdncjsoqmlh.supabase.co"
SUPABASE_KEY = "sb_publishable_tc2XxJANYH57uQHLapU2RQ_S1YmGztr" # ※実際は秘密鍵が必要な場合があります
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# カテゴリ定義と判定用キーワード
CATEGORIES_MAP = {
    "infra": ["AWS", "Docker", "Kubernetes", "Terraform", "Linux", "Azure", "Ansible", "GCP", "Network", "インフラ", "ネットワーク"],
    "backend": ["バックエンド", "Python", "Go", "Rust", "Ruby", "Node.js", "Java", "PHP", "SQL"],
    "frontend": ["フロントエンド", "開発", "React", "TypeScript", "Next.js", "Vue", "TailwindCSS", "JavaScript"],
    "common": ["Architecture", "設計", "DDD", "Git", "GitHub", "技術書", "書籍", "読書"]
}

def determine_categories(title, articles):
    """
    タイトルと記事のタグの両方からジャンルを判定する
    """
    matched = set()
    title_lower = title.lower()
    
    # 1. 記事のタグから判定 (articlesテーブルのtags列を想定)
    all_tags = []
    for a in articles:
        tags = a.get('tags', [])
        if isinstance(tags, list):
            all_tags.extend([t.lower() for t in tags])
        elif isinstance(tags, str):
            all_tags.append(tags.lower())

    for cat_name, keywords in CATEGORIES_MAP.items():
        # タイトルチェック
        if any(kw.lower() in title_lower for kw in keywords):
            matched.add(cat_name)
            continue
        
        # 記事のタグチェック
        if any(kw.lower() in all_tags for kw in keywords):
            matched.add(cat_name)
            
    return list(matched)

def get_period_payload(all_data, target_year, target_month=None):
    merged_books = {}
    
    for item in all_data:
        asin = item['asin']
        articles = item.get('articles', [])
        if not isinstance(articles, list): articles = [articles] if articles else []

        filtered_articles = []
        for a in articles:
            if not a.get('published_at'): continue
            try:
                pub_date = date.fromisoformat(a['published_at'][:10])
                if target_month:
                    if pub_date.year == target_year and pub_date.month == target_month:
                        filtered_articles.append(a)
                else:
                    if pub_date.year == target_year:
                        filtered_articles.append(a)
            except: continue

        if not filtered_articles: continue

        if asin not in merged_books:
            merged_books[asin] = {
                "asin": asin, "title": item['title'], "image_url": item.get('image_url'),
                "amazon_url": item.get('amazon_url'), "articles": []
            }
        merged_books[asin]["articles"].extend(filtered_articles)

    payload = []
    for asin, book in merged_books.items():
        unique_articles = {a['url']: a for a in book['articles']}.values()
        unique_articles = sorted(list(unique_articles), key=lambda x: x.get('likes_count', 0), reverse=True)

        mention_count = len(unique_articles)
        total_likes = sum(a.get('likes_count', 0) for a in unique_articles)
        points = mention_count + math.floor(total_likes / 100)

        # 【改修ポイント】タイトルと全記事のタグを使ってカテゴリ判定
        matched_categories = determine_categories(book['title'], list(unique_articles))

        payload.append({
            "asin": asin, "title": book['title'], "image_url": book['image_url'],
            "amazon_url": book['amazon_url'], "total_points": points,
            "mention_count": mention_count, "total_likes": total_likes,
            "categories": matched_categories,
            "top_articles": [{"title": a['title'], "url": a['url'], "likes": a['likes_count']} for a in unique_articles[:3]]
        })
    
    payload.sort(key=lambda x: x['total_points'], reverse=True)
    for i, item in enumerate(payload): item['rank'] = i + 1
    return payload

def get_filtered_payload_all(all_data):
    """全期間用の集計"""
    merged_books = {}
    for item in all_data:
        asin = item['asin']
        articles = item.get('articles', [])
        if not isinstance(articles, list): articles = [articles] if articles else []
        if not articles: continue
        if asin not in merged_books:
            merged_books[asin] = {
                "asin": asin, "title": item['title'], "image_url": item.get('image_url'),
                "amazon_url": item.get('amazon_url'), "articles": articles
            }
        else:
            merged_books[asin]["articles"].extend(articles)
    
    payload = []
    for asin, book in merged_books.items():
        unique_articles = {a['url']: a for a in book['articles']}.values()
        unique_articles = sorted(list(unique_articles), key=lambda x: x.get('likes_count', 0), reverse=True)
        mention_count = len(unique_articles)
        total_likes = sum(a.get('likes_count', 0) for a in unique_articles)
        points = mention_count + math.floor(total_likes / 100)
        
        # 【改修ポイント】全期間でもタグ判定を適用
        matched_categories = determine_categories(book['title'], list(unique_articles))

        payload.append({
            "asin": asin, "title": book['title'], "image_url": book['image_url'],
            "amazon_url": book['amazon_url'], "total_points": points,
            "mention_count": mention_count, "total_likes": total_likes,
            "categories": matched_categories,
            "top_articles": [{"title": a['title'], "url": a['url'], "likes": a['likes_count']} for a in unique_articles[:3]],
            "period": "all"
        })
    payload.sort(key=lambda x: x['total_points'], reverse=True)
    for i, item in enumerate(payload): item['rank'] = i + 1
    return payload

def update_rankings():
    print("🚀 ジャンル判定強化版ランキング集計始動...")
    today = date.today()

    this_month_y, this_month_m = today.year, today.month
    first_day_this_month = today.replace(day=1)
    last_month_date = first_day_this_month - timedelta(days=1)
    last_month_y, last_month_m = last_month_date.year, last_month_date.month
    this_year, last_year = today.year, today.year - 1

    # booksを取得する際、紐づくarticlesの全列（tags含む）を取得
    res = supabase.table("books").select("*, articles(*)").eq("status", "completed").execute()
    all_data = res.data
    if not all_data: return

    p_this_month = get_period_payload(all_data, this_month_y, this_month_m)
    for item in p_this_month: item['period'] = f"{this_month_y}-{this_month_m:02d}"

    p_last_month = get_period_payload(all_data, last_month_y, last_month_m)
    for item in p_last_month: item['period'] = f"{last_month_y}-{last_month_m:02d}"

    p_this_year = get_period_payload(all_data, this_year)
    for item in p_this_year: item['period'] = str(this_year)

    p_last_year = get_period_payload(all_data, last_year)
    for item in p_last_year: item['period'] = str(last_year)

    p_all = get_filtered_payload_all(all_data)

    tasks = [
        ("book_rankings", p_all),
        ("monthly_rankings", p_this_month + p_last_month),
        ("yearly_rankings", p_this_year + p_last_year)
    ]

    for table_name, data in tasks:
        print(f"🧹 {table_name} をリセット中...")
        supabase.table(table_name).delete().neq("asin", "empty").execute()
        if data:
            print(f"📝 {table_name} に {len(data)} 件挿入中 (タグ判定適用済)...")
            for i in range(0, len(data), 100):
                supabase.table(table_name).insert(data[i:i+100]).execute()

    print("✨ すべての集計が完了しました！フロントエンドを確認してください。")

if __name__ == "__main__":
    update_rankings()