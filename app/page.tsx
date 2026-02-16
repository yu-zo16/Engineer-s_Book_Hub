"use client";

import { useEffect, useState } from 'react';
import { supabase } from './lib/supabase';
import { Search, ExternalLink, ThumbsUp, MessageCircle, Trophy, X } from 'lucide-react';

const CATEGORIES = {
  ALL: { label: "すべて", id: "all" },
  INFRA: { label: "インフラ", id: "infra" },
  BACKEND: { label: "バックエンド", id: "backend" },
  FRONTEND: { label: "フロントエンド", id: "frontend" },
  COMMON: { label: "共通・書籍", id: "common" },
};

export default function Home() {
  // --- 期間の定数 ---
  const currentYear = "2026";
  const lastYear = "2025";
  const currentMonthStr = "2026-02";
  const lastMonthStr = "2026-01";

  // --- ステート管理 ---
  const [period, setPeriod] = useState("all");     // all, yearly, monthly
  const [detail, setDetail] = useState("all");     // 2026, 2026-02 など
  const [activeTab, setActiveTab] = useState("ALL"); // ALL, INFRA, BACKEND...
  const [searchQuery, setSearchQuery] = useState("");
  const [books, setBooks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // --- データ取得ロジック (ここが修正の肝です) ---
  useEffect(() => {
    async function fetchRankings() {
      setLoading(true);

      // 1. 参照テーブルの決定
      let tableName = 'book_rankings';
      if (period === 'monthly') tableName = 'monthly_rankings';
      if (period === 'yearly') tableName = 'yearly_rankings';

      // 2. クエリの初期化
      let query = supabase
        .from(tableName)
        .select('*')
        .order('total_points', { ascending: false });

      // 3. 【期間設定】を適用
      // monthly_rankings や yearly_rankings の場合は period カラムで絞り込む
      if (period !== 'all') {
        let filterValue = detail;
        if (detail === 'all') {
          filterValue = period === 'monthly' ? currentMonthStr : currentYear;
        }
        query = query.eq('period', filterValue);
      }

      // 4. 【ジャンル設定】を適用 (ここが連動のポイント)
      // activeTabが "ALL" 以外なら、どのテーブルに対しても絞り込みをかける
      if (activeTab !== "ALL") {
        const categoryId = CATEGORIES[activeTab as keyof typeof CATEGORIES].id;
        // Postgresの配列型(categories)にcategoryIdが含まれているか
        query = query.contains('categories', [categoryId]);
      }

      const { data, error } = await query;

      if (!error) {
        setBooks(data || []);
      } else {
        console.error("Supabase error:", error);
      }
      setLoading(false);
    }

    fetchRankings();
    // [activeTab, period, detail] のいずれかが変わるたびに必ず再取得
  }, [activeTab, period, detail]);

  // クライアントサイドでのタイトル検索フィルタ
  const displayBooks = books.filter((book) =>
    book.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-white text-slate-800 font-sans pb-20">
      <header className="border-b border-slate-100 mb-8">
        <div className="max-w-6xl mx-auto px-4 h-20 flex items-center justify-center">
          <h1 className="text-2xl font-black tracking-tighter italic uppercase text-slate-900">Engineer's Book Hub</h1>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4">
        {/* 検索バー */}
        <div className="relative mb-12 max-w-2xl mx-auto">
          <input 
            type="text" 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="タイトルやキーワードで検索..." 
            className="w-full border-2 border-orange-400 rounded-2xl py-4 px-14 focus:outline-none shadow-md shadow-orange-100 text-lg transition-all focus:ring-4 focus:ring-orange-100"
          />
          <Search className="absolute left-5 top-1/2 -translate-y-1/2 text-orange-500 w-6 h-6" />
        </div>

        {/* 期間メインタブ */}
        <div className="flex items-center justify-center gap-2 mb-6 max-w-xl mx-auto bg-slate-100 p-1.5 rounded-2xl font-bold">
          <button onClick={() => { setPeriod('all'); setDetail('all'); }} className={`flex-1 text-center py-2.5 rounded-xl text-sm transition-all ${period === 'all' ? 'bg-white shadow-sm text-slate-900' : 'text-slate-500 hover:text-slate-700'}`}>全期間</button>
          <button onClick={() => { setPeriod('yearly'); setDetail(currentYear); }} className={`flex-1 text-center py-2.5 rounded-xl text-sm transition-all ${period === 'yearly' ? 'bg-white shadow-sm text-slate-900' : 'text-slate-500 hover:text-slate-700'}`}>年間</button>
          <button onClick={() => { setPeriod('monthly'); setDetail(currentMonthStr); }} className={`flex-1 text-center py-2.5 rounded-xl text-sm transition-all ${period === 'monthly' ? 'bg-white shadow-sm text-slate-900' : 'text-slate-500 hover:text-slate-700'}`}>月間</button>
        </div>

        {/* 年・月 サブボタン */}
        {period !== 'all' && (
          <div className="flex justify-center gap-3 mb-10">
            {(period === 'yearly' ? [currentYear, lastYear] : [currentMonthStr, lastMonthStr]).map((v) => (
              <button 
                key={v} 
                onClick={() => setDetail(v)} 
                className={`px-8 py-2.5 rounded-full text-xs font-black border-2 transition-all ${detail === v ? 'border-slate-800 bg-slate-800 text-white' : 'border-slate-200 text-slate-400 hover:border-slate-300'}`}
              >
                {v === currentYear ? "2026年" : v === lastYear ? "2025年" : v === currentMonthStr ? "2月" : "1月"}
              </button>
            ))}
          </div>
        )}

        {/* ジャンルタブ */}
        <div className="flex items-center justify-center gap-3 mb-10 overflow-x-auto pb-2 scrollbar-hide">
          {Object.entries(CATEGORIES).map(([key, value]) => (
            <button 
              key={key} 
              onClick={() => setActiveTab(key)}
              className={`px-8 py-3 rounded-xl text-sm font-bold transition-all duration-200 ${
                activeTab === key ? 'bg-orange-500 text-white shadow-lg scale-105' : 'bg-slate-100 text-slate-500 hover:bg-slate-200'
              }`}
            >
              {value.label}
            </button>
          ))}
        </div>

        {/* ランキングの見出し */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-2 font-black text-xl text-slate-700">
            <Trophy className="text-orange-500 w-6 h-6" />
            <span>{CATEGORIES[activeTab as keyof typeof CATEGORIES].label} ランキング</span>
            <span className="text-sm font-medium text-slate-400 ml-2">
              ({period === 'all' ? '全期間' : detail})
            </span>
          </div>
          <div className="text-sm font-bold text-slate-400">
            {loading ? "読み込み中..." : `${displayBooks.length} 件`}
          </div>
        </div>

        {/* 書籍カード一覧 */}
        {loading ? (
          <div className="flex justify-center items-center py-20 font-bold text-slate-300 animate-pulse text-lg tracking-widest">
            LOADING RANKING...
          </div>
        ) : displayBooks.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {displayBooks.map((book, index) => (
              <div key={book.asin} className="bg-white border border-slate-100 rounded-[2.5rem] overflow-hidden hover:shadow-2xl transition-all duration-300 flex flex-col border-b-4 border-b-slate-200">
                <div className="relative h-64 bg-slate-50 flex items-center justify-center p-8">
                  <div className="absolute top-6 left-6 z-10 bg-white/90 w-9 h-9 rounded-full flex items-center justify-center font-black text-orange-500 border border-orange-100">
                    {index + 1}
                  </div>
                  {book.image_url ? (
                    <img src={book.image_url} alt={book.title} className="max-h-full shadow-2xl" />
                  ) : (
                    <div className="w-32 h-44 bg-slate-200 rounded-lg flex items-center justify-center text-slate-400 text-[10px]">No Image</div>
                  )}
                </div>

                <div className="p-8 flex-1 flex flex-col">
                  <a href={book.amazon_url} target="_blank" rel="noopener noreferrer" className="block mb-6 h-12">
                    <h3 className="font-bold text-[1.1rem] leading-snug line-clamp-2 underline decoration-yellow-300 decoration-4 underline-offset-[-4px] hover:decoration-orange-300 transition-all">
                      {book.title}
                    </h3>
                  </a>

                  <div className="mb-8 space-y-3">
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest flex items-center gap-1.5">
                      <MessageCircle className="w-3.5 h-3.5" /> Featured Mentions
                    </p>
                    {book.top_articles?.slice(0, 3).map((art: any, i: number) => (
                      <a key={i} href={art.url} target="_blank" rel="noopener noreferrer" className="text-[11px] text-blue-600 font-medium line-clamp-1 hover:text-orange-600 transition-colors">
                        • {art.title}
                      </a>
                    ))}
                  </div>

                  <div className="mt-auto pt-6 border-t border-slate-100 flex items-center justify-between">
                    <div className="flex items-center gap-1.5 text-orange-600 font-black text-2xl tracking-tighter">
                      <ThumbsUp className="w-4.5 h-4.5 fill-orange-50" />
                      {book.total_points} pt
                    </div>
                    <a href={book.amazon_url} target="_blank" rel="noopener noreferrer" className="bg-[#0f172a] text-white px-6 py-2.5 rounded-xl text-xs font-bold hover:bg-orange-600 transition-all shadow-xl">
                      Amazon <ExternalLink className="w-3 h-3 inline ml-1" />
                    </a>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-24 bg-slate-50 rounded-[3.5rem] border-2 border-dashed border-slate-200 text-slate-400 font-bold">
            この期間の「{CATEGORIES[activeTab as keyof typeof CATEGORIES].label}」データはまだありません 😢
          </div>
        )}
      </main>
    </div>
  );
}