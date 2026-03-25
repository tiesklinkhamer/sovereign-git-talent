"use client";

import { useEffect, useState } from "react";
import { Search, Plus, Trash2, Tag, ShieldAlert, Activity, Check, Filter } from "lucide-react";
import { motion } from "framer-motion";

export default function DiscoverySettings() {
  const [keywords, setKeywords] = useState<any[]>([]);
  const [newKeyword, setNewKeyword] = useState("");
  const [newCategory, setNewCategory] = useState("general");
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState(false);

  useEffect(() => {
    fetchKeywords();
  }, []);

  const fetchKeywords = async () => {
    try {
      // In a real app we'd have a GET /discovery/keywords
      // For now we'll simulate or add the GET endpoint if possible.
      // Let's assume we can fetch them.
      const res = await fetch("${process.env.NEXT_PUBLIC_API_URL}/discovery/keywords/list");
      if (res.ok) {
        const data = await res.json();
        setKeywords(data.keywords || []);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newKeyword) return;
    setAdding(true);
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/discovery/keywords?keyword=${newKeyword}&category=${newCategory}`, {
        method: "POST"
      });
      if (res.ok) {
        setNewKeyword("");
        // In a real app we'd refresh or the backend would return the new list
        setKeywords([...keywords, { keyword: newKeyword, category: newCategory, is_active: true }]);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setAdding(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in duration-700">
      <header>
        <h1 className="text-3xl font-bold tracking-tight text-white mb-2 italic uppercase">Algorithmic <span className="text-blue-500">Discovery</span> Nets</h1>
        <p className="text-zinc-400">Manage the technical keywords used to automatically hunt for emerging defense talent.</p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {/* Form */}
        <div className="md:col-span-1 space-y-6">
          <div className="glass p-6 rounded-2xl space-y-4">
            <h2 className="text-sm font-bold text-zinc-500 uppercase flex items-center gap-2">
              <Plus className="w-4 h-4" /> Add New Net
            </h2>
            <form onSubmit={handleAdd} className="space-y-4">
              <div className="space-y-1">
                <label className="text-[10px] font-bold text-zinc-500 uppercase px-1">Keyword</label>
                <input 
                  type="text" 
                  className="w-full bg-black/30 border border-white/10 rounded-xl px-4 py-2 text-white focus:outline-none focus:ring-1 focus:ring-blue-500 transition-all text-sm"
                  placeholder="e.g. UAV, PX4, SDR"
                  value={newKeyword}
                  onChange={(e) => setNewKeyword(e.target.value)}
                />
              </div>
              <div className="space-y-1">
                <label className="text-[10px] font-bold text-zinc-500 uppercase px-1">Category</label>
                <select 
                  className="w-full bg-black/30 border border-white/10 rounded-xl px-4 py-2 text-white focus:outline-none focus:ring-1 focus:ring-blue-500 transition-all text-sm appearance-none"
                  value={newCategory}
                  onChange={(e) => setNewCategory(e.target.value)}
                >
                  <option value="general">General Dual-Use</option>
                  <option value="UAV">Unmanned Systems</option>
                  <option value="AI">Defense AI / ML</option>
                  <option value="Crypto">Cryptography / Cyber</option>
                  <option value="SDR">Electronic Warfare / SDR</option>
                </select>
              </div>
              <button 
                type="submit" 
                disabled={adding}
                className="w-full py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs transition-all shadow-lg flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {adding ? <Activity className="w-3 h-3 animate-spin" /> : <Tag className="w-3 h-3" />}
                Deploy Keyword
              </button>
            </form>
          </div>

          <div className="p-6 border border-blue-500/10 bg-blue-500/5 rounded-2xl">
            <div className="flex items-center gap-3 text-blue-400 mb-2">
              <ShieldAlert className="w-5 h-5" />
              <h3 className="text-xs font-bold uppercase">Rate Limit Info</h3>
            </div>
            <p className="text-[11px] text-zinc-400 leading-relaxed">
              GitHub Search API allows 30 requests per minute. Keywords are polled sequentially every 4-12 hours to ensure stability.
            </p>
          </div>
        </div>

        {/* List */}
        <div className="md:col-span-2 space-y-4">
          <h2 className="text-sm font-bold text-zinc-500 uppercase tracking-widest flex items-center gap-2 px-1">
            Active Watch List
            <div className="h-px flex-1 bg-white/5" />
          </h2>

          <div className="grid grid-cols-1 gap-3">
            {loading ? (
              [1, 2, 3].map(i => <div key={i} className="h-16 bg-white/5 animate-pulse rounded-xl" />)
            ) : keywords.length > 0 ? (
              keywords.map((kw, i) => (
                <motion.div 
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.05 }}
                  key={kw.keyword} 
                  className="glass px-6 py-4 rounded-xl flex items-center justify-between group hover:border-blue-500/20 transition-all"
                >
                  <div className="flex items-center gap-4">
                    <div className="p-2 rounded-lg bg-white/5 text-zinc-500 group-hover:text-blue-400 transition-colors">
                      <Filter className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="text-sm font-bold text-white tracking-tight">{kw.keyword}</div>
                      <div className="text-[10px] text-zinc-500 font-bold uppercase">{kw.category}</div>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-6">
                    <div className="flex items-center gap-1.5 text-[10px] font-bold text-emerald-500/70">
                      <Check className="w-3 h-3" />
                      ACTIVE
                    </div>
                    <button className="p-2 text-zinc-600 hover:text-red-400 hover:bg-red-400/10 rounded-lg transition-all opacity-0 group-hover:opacity-100">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </motion.div>
              ))
            ) : (
              <div className="text-center py-20 glass rounded-2xl border-dashed">
                <p className="text-zinc-500 text-sm">No discovery keywords deployed yet.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
