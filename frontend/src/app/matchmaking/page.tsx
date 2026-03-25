"use client";

import { useState } from "react";
import { Search, Sparkles, MapPin, Briefcase, ExternalLink, Activity, Target, ShieldCheck } from "lucide-react";
import { motion } from "framer-motion";

export default function MatchmakingPage() {
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query) return;
    setLoading(true);
    try {
      const res = await fetch("${process.env.NEXT_PUBLIC_API_URL}/matchmaking/suggest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ capability_query: query }),
      });
      const data = await res.json();
      setSuggestions(data.suggestions || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-500 max-w-5xl mx-auto">
      <header className="text-center space-y-4 py-10">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 text-xs font-bold uppercase tracking-widest">
          <Target className="w-3.5 h-3.5" />
          Capability Matchmaking
        </div>
        <h1 className="text-4xl font-bold tracking-tight text-white italic capitalize">
          Find Your Next <span className="text-blue-500">Defense Tech</span> Hire
        </h1>
        <p className="text-zinc-400 max-w-2xl mx-auto">
          Skip keywords. Search by technical mission, project requirements, or niche domain expertise.
        </p>

        <form onSubmit={handleSearch} className="max-w-2xl mx-auto pt-6">
          <div className="relative group">
            <div className="absolute -inset-1 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl blur opacity-25 group-hover:opacity-50 transition duration-1000"></div>
            <div className="relative flex items-center bg-zinc-900 border border-white/10 rounded-2xl p-2 pr-3">
              <Search className="w-5 h-5 ml-4 text-zinc-500" />
              <input 
                type="text" 
                placeholder="Ex: Drone swarm communication expert with ROS2 experience..." 
                className="flex-1 bg-transparent border-none outline-none text-white px-4 py-3 text-sm placeholder:text-zinc-600"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
              <button 
                type="submit"
                disabled={loading}
                className="bg-blue-600 hover:bg-blue-500 text-white px-6 py-2 rounded-xl text-sm font-bold transition-all flex items-center gap-2 disabled:opacity-50"
              >
                {loading ? <Activity className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                Analyze
              </button>
            </div>
          </div>
        </form>
      </header>

      {loading ? (
        <div className="flex flex-col items-center justify-center p-20 gap-4">
          <Activity className="w-10 h-10 text-blue-500 animate-spin" />
          <p className="text-zinc-500 text-sm font-medium animate-pulse">Consulting Intelligence Engine...</p>
        </div>
      ) : suggestions.length > 0 ? (
        <div className="grid grid-cols-1 gap-6 pb-20">
          <h2 className="text-sm font-bold text-zinc-500 uppercase tracking-widest flex items-center gap-2">
            Top Talent Recommendations
            <div className="h-px flex-1 bg-white/5" />
          </h2>
          
          {suggestions.map((profile, i) => (
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              key={profile.id} 
              className="glass p-8 rounded-3xl hover:border-blue-500/30 transition-all group flex flex-col md:flex-row gap-8"
            >
              <div className="shrink-0 flex flex-col items-center gap-4">
                <img 
                  src={`https://github.com/${profile.github_username}.png`} 
                  alt={profile.github_username}
                  className="w-20 h-20 rounded-2xl border-2 border-white/10 group-hover:border-blue-500/50 transition-colors shadow-2xl"
                />
                <div className="text-center">
                  <div className="text-2xl font-bold text-white leading-none">
                    {profile.defense_relevance_score.toFixed(0)}
                  </div>
                  <div className="text-[10px] text-zinc-500 font-bold uppercase tracking-tighter">Match Rank</div>
                </div>
              </div>

              <div className="flex-1 space-y-4">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="text-xl font-bold text-white flex items-center gap-3">
                      {profile.github_username}
                      {profile.is_claimed && (
                        <ShieldCheck className="w-5 h-5 text-blue-400" />
                      )}
                    </h3>
                    <div className="flex flex-wrap gap-4 mt-1 text-sm text-zinc-400">
                      <span className="flex items-center gap-1.5"><MapPin className="w-3.5 h-3.5" /> {profile.location || "Remote"}</span>
                      <span className="flex items-center gap-1.5"><Briefcase className="w-3.5 h-3.5" /> {profile.company || "Stealth"}</span>
                    </div>
                  </div>
                  {profile.open_to_work && (
                    <span className="bg-emerald-500/10 text-emerald-400 text-[10px] font-bold px-3 py-1 rounded-full border border-emerald-500/20 uppercase tracking-widest">
                      Accepting Leads
                    </span>
                  )}
                </div>

                <div className="bg-white/5 rounded-2xl p-5 text-sm text-zinc-300 leading-relaxed border border-white/5 shadow-inner italic">
                  &ldquo;{profile.brief_summary ? profile.brief_summary.split('\n')[0] : "No summary available."}&rdquo;
                </div>

                <div className="flex justify-between items-center pt-2">
                  <div className="flex gap-2">
                    <span className="px-3 py-1 rounded-md bg-zinc-800 text-zinc-400 text-[10px] font-bold uppercase tracking-wider">Signals: {profile.defense_relevance_score > 10 ? 'High Confidence' : 'Emerging'}</span>
                  </div>
                  <a 
                    href={`https://github.com/${profile.github_username}`} 
                    target="_blank" 
                    rel="noreferrer"
                    className="text-xs font-bold text-blue-400 hover:text-white flex items-center gap-1.5 transition-colors group/btn"
                  >
                    Full Dossier 
                    <ExternalLink className="w-3.5 h-3.5 group-hover/btn:translate-x-0.5 group-hover/btn:-translate-y-0.5 transition-transform" />
                  </a>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      ) : query && !loading ? (
        <div className="text-center p-20 glass rounded-3xl border-dashed">
          <p className="text-zinc-500">No high-confidence matches found for that specific capability. Try broadening your criteria.</p>
        </div>
      ) : null}
    </div>
  );
}
