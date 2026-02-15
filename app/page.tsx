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
  const [activeTab, setActiveTab] = useState("ALL");
  const [searchQuery, setSearchQuery] = useState(""); // 検索ワード用ステート
  const [books, setBooks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchRankings() {
      setLoading(true);
      let query = supabase
        .from('book_rankings')
        .select('*')
        .order('total_points', { ascending: false });

      if (activeTab !== "ALL") {
        const categoryId = CATEGORIES[activeTab as keyof typeof CATEGORIES].id;
        query = query.contains('categories', [categoryId]);
      }

      const { data, error } = await query;
      if (!error) setBooks(data || []);
      setLoading(false);
    }
    fetchRankings();
  }, [activeTab]);

  // --- 検索フィルタリングロジック ---
  // カテゴリで絞り込まれたbooksに対して、さらに検索ワードでフィルタをかける
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
        {/* --- 検索バー (Controlled Input) --- */}
        <div className="relative mb-12 max-w-2xl mx-auto">
          <input 
            type="text" 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="タイトルやキーワードで技術書を検索..." 
            className="w-full border-2 border-orange-400 rounded-2xl py-4 px-14 focus:outline-none shadow-md shadow-orange-100 text-lg transition-all focus:ring-4 focus:ring-orange-100"
          />
          <Search className="absolute left-5 top-1/2 -translate-y-1/2 text-orange-500 w-6 h-6" />
          
          {/* 文字が入っている時だけ消去ボタンを表示 */}
          {searchQuery && (
            <button 
              onClick={() => setSearchQuery("")}
              className="absolute right-5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>

        {/* カテゴリタブ */}
        <div className="flex items-center justify-center gap-3 mb-10 overflow-x-auto pb-2 scrollbar-hide">
          {Object.entries(CATEGORIES).map(([key, value]) => (
            <button 
              key={key} 
              onClick={() => {
                setActiveTab(key);
                // カテゴリを変えた時に検索をクリアしたい場合はここに追加
              }}
              className={`px-8 py-3 rounded-xl text-sm font-bold transition-all duration-200 ${
                activeTab === key 
                ? 'bg-orange-500 text-white shadow-lg shadow-orange-200 scale-105' 
                : 'bg-slate-100 text-slate-500 hover:bg-slate-200'
              }`}
            >
              {value.label}
            </button>
          ))}
        </div>

        {/* ランキングタイトル & 件数表示 */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-2 font-black text-xl text-slate-700">
            <Trophy className="text-orange-500 w-6 h-6" />
            <span>{CATEGORIES[activeTab as keyof typeof CATEGORIES].label} ランキング</span>
          </div>
          <div className="text-sm font-bold text-slate-400">
            {displayBooks.length} 件ヒット
          </div>
        </div>

        {loading ? (
          <div className="flex justify-center items-center py-20 font-bold text-slate-300 animate-pulse text-lg">
            RANKING LOADING...
          </div>
        ) : displayBooks.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {displayBooks.map((book, index) => (
              <div key={book.asin} className="bg-white border border-slate-100 rounded-[2.5rem] overflow-hidden hover:shadow-2xl hover:shadow-slate-200 transition-all duration-300 flex flex-col group border-b-4 border-b-slate-200">
                
                {/* 書影エリア */}
                <div className="relative h-64 bg-slate-50 flex items-center justify-center p-8">
                  <div className="absolute top-6 left-6 z-10 bg-white/90 backdrop-blur w-9 h-9 rounded-full flex items-center justify-center font-black text-orange-500 shadow-sm border border-orange-100">
                    {index + 1}
                  </div>
                  {book.image_url ? (
                    <img src={book.image_url} alt={book.title} className="max-h-full shadow-2xl group-hover:rotate-2 transition-transform duration-500" />
                  ) : (
                    <div className="w-32 h-44 bg-slate-200 rounded-lg" />
                  )}
                </div>

                <div className="p-8 flex-1 flex flex-col">
                  {/* 書籍タイトル */}
                  <a href={book.amazon_url} target="_blank" rel="noopener noreferrer" className="block mb-6 group/link">
                    <h3 className="font-bold text-[1.1rem] leading-snug min-h-[3.3rem] line-clamp-2 decoration-yellow-300 decoration-4 underline-offset-[-4px] group-hover/link:underline transition-all">
                      {book.title}
                    </h3>
                  </a>

                  {/* Qiita記事リスト */}
                  <div className="mb-8 space-y-3">
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-[0.2em] flex items-center gap-1.5 mb-3">
                      <MessageCircle className="w-3.5 h-3.5" /> 紹介されている人気記事
                    </p>
                    {book.top_articles?.map((art: any, i: number) => (
                      <a key={i} href={art.url} target="_blank" rel="noopener noreferrer" className="text-[11px] text-blue-600 hover:text-blue-800 font-medium flex items-start gap-1.5 leading-relaxed">
                        <span className="text-blue-300 mt-0.5">•</span>
                        <span className="line-clamp-1">{art.title}</span>
                        <span className="text-slate-400 font-normal ml-auto flex-shrink-0">({art.likes}❤️)</span>
                      </a>
                    ))}
                  </div>

                  {/* スコアとAmazon */}
                  <div className="mt-auto pt-6 border-t border-slate-100 flex items-center justify-between">
                    <div className="flex flex-col">
                      <div className="flex items-center gap-1.5 text-orange-600">
                        <ThumbsUp className="w-4.5 h-4.5 fill-orange-50" />
                        <span className="font-black text-2xl tracking-tighter">{book.total_points} pt</span>
                      </div>
                      <span className="text-[9px] text-slate-400 font-extrabold uppercase tracking-widest">Score</span>
                    </div>
                    
                    <a 
                      href={book.amazon_url} 
                      target="_blank" 
                      className="bg-[#0f172a] text-white px-6 py-2.5 rounded-xl text-xs font-bold hover:bg-orange-600 transition-all shadow-xl shadow-slate-200"
                    >
                      Amazon
                      <ExternalLink className="w-3.5 h-3.5" />
                    </a>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-20 text-slate-400 font-bold">
            一致する書籍が見つかりませんでした 😢
          </div>
        )}
      </main>
    </div>
  );
}