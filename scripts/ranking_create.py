import math
from supabase import create_client

# --- 設定 ---
SUPABASE_URL = "https://dndowbpxacdncjsoqmlh.supabase.co"
SUPABASE_KEY = "sb_publishable_tc2XxJANYH57uQHLapU2RQ_S1YmGztr"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# カテゴリ定義
CATEGORIES = {
    "infra": ["AWS", "Docker", "Kubernetes", "Terraform", "Linux", "Azure", "Ansible", "GCP", "Network"],
    "backend": ["Python", "Go", "Rust", "Ruby", "Node.js", "Java", "PHP", "SQL"],
    "frontend": ["React", "TypeScript", "Next.js", "Vue", "TailwindCSS", "JavaScript"],
    "common": ["Architecture", "設計", "DDD", "Git", "GitHub", "技術書", "書籍", "読書"]
}

def update_rankings():
    print("📊 ランキング集計を開始します...")

    # 1. データの取得 (books と紐づく articles)
    # ※ リレーションが設定されている前提
    res = supabase.table("books").select("*, articles(*)").eq("status", "completed").execute()
    all_data = res.data

    if not all_data:
        print("データが見つかりませんでした。")
        return

    # 2. ASIN単位でマージ
    merged_books = {}
    for item in all_data:
        asin = item['asin']
        articles = item.get('articles', [])
        if not isinstance(articles, list): # 1対1対策
            articles = [articles] if articles else []

        if asin not in merged_books:
            merged_books[asin] = {
                "asin": asin,
                "title": item['title'],
                "image_url": item.get('image_url'),
                "amazon_url": item.get('amazon_url'),
                "all_articles": []
            }
        
        # 記事を追加（重複URLは排除）
        merged_books[asin]["all_articles"].extend(articles)

    # 3. 集計ロジック適用
    ranking_payload = []
    for asin, book in merged_books.items():
        # ユニークな記事に絞り込み
        unique_articles = {a['url']: a for a in book['all_articles']}.values()
        unique_articles = list(unique_articles)

        # いいね順ソート
        unique_articles.sort(key=lambda x: x.get('likes_count', 0), reverse=True)

        # ポイント計算
        mention_count = len(unique_articles)
        total_likes = sum(a.get('likes_count', 0) for a in unique_articles)
        points = mention_count + math.floor(total_likes / 100)

        # カテゴリ判定
        matched_categories = []
        title_lower = book['title'].lower()
        for cat_name, keywords in CATEGORIES.items():
            if any(kw.lower() in title_lower for kw in keywords):
                matched_categories.append(cat_name)

        # 上位3記事のJSON作成
        top_articles = [
            {"title": a['title'], "url": a['url'], "likes": a['likes_count']}
            for a in unique_articles[:3]
        ]

        ranking_payload.append({
            "asin": asin,
            "title": book['title'],
            "image_url": book['image_url'],
            "amazon_url": book['amazon_url'],
            "total_points": points,
            "mention_count": mention_count,
            "total_likes": total_likes,
            "categories": matched_categories,
            "top_articles": top_articles
        })

    # 4. DB反映 (既存のランキングを空にしてから挿入)
    # ※ UPSERTでも良いですが、順位変動が激しい場合は全入れ替えが確実です
    if ranking_payload:
        # 一旦削除（必要に応じて）
        supabase.table("book_rankings").delete().neq("asin", "empty").execute()
        # 一括挿入
        supabase.table("book_rankings").insert(ranking_payload).execute()
        print(f"✅ {len(ranking_payload)} 件の書籍を book_rankings に反映しました。")

if __name__ == "__main__":
    update_rankings()