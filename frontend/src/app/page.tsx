"use client";

import { useEffect, useState } from "react";
import { Search, MapPin, Briefcase, ExternalLink, Activity, Github } from "lucide-react";
import { motion } from "framer-motion";

export default function Home() {
  const [profiles, setProfiles] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [minScore, setMinScore] = useState(0);

  useEffect(() => {
    fetchProfiles();
  }, [search, minScore]);

  const fetchProfiles = async () => {
    setLoading(true);
    try {
      // Build query string
      const params = new URLSearchParams();
      if (search) params.append("location", search);
      if (minScore > 0) params.append("min_score", minScore.toString());
      
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/search/profiles?${params.toString()}`);
      const data = await res.json();
      setProfiles(data.profiles || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <header className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Talent Database</h1>
          <p className="text-zinc-400">Discover and track top engineering talent in the defense ecosystem.</p>
        </div>
        
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
            <input 
              type="text" 
              placeholder="Search by location..." 
              className="bg-zinc-900/50 border border-white/10 rounded-full pl-9 pr-4 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 w-full md:w-64 transition-all"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <select 
            className="bg-zinc-900/50 border border-white/10 rounded-full px-4 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all"
            value={minScore}
            onChange={(e) => setMinScore(Number(e.target.value))}
          >
            <option value={0}>Any Score</option>
            <option value={5}>Score &gt; 5</option>
            <option value={10}>Score &gt; 10</option>
            <option value={20}>Score &gt; 20</option>
          </select>
        </div>
      </header>

      {loading ? (
        <div className="flex items-center justify-center p-20">
          <Activity className="w-8 h-8 text-blue-500 animate-spin" />
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {profiles.length === 0 ? (
            <div className="col-span-1 lg:col-span-2 text-center p-12 glass rounded-2xl border-dashed">
              <p className="text-zinc-400">No profiles found matching your criteria.</p>
            </div>
          ) : (
            profiles.map((profile, i) => (
              <motion.div 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
                key={profile.id} 
                className="glass p-6 rounded-2xl hover:border-blue-500/30 transition-all group"
              >
                <div className="flex justify-between items-start mb-4">
                  <div className="flex items-center gap-4">
                    <img 
                      src={`https://github.com/${profile.github_username}.png`} 
                      alt={profile.github_username}
                      className="w-12 h-12 rounded-full border border-white/10 group-hover:border-blue-500/50 transition-colors"
                    />
                    <div>
                      <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                        {profile.github_username}
                        {profile.open_to_work && (
                          <span className="px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 text-xs font-medium border border-emerald-500/20">
                            Open to Work
                          </span>
                        )}
                      </h3>
                      <p className="text-sm text-zinc-400 flex items-center gap-2">
                        {profile.known_affiliation || "Unknown Affiliation"}
                      </p>
                    </div>
                  </div>
                  <div className="flex flex-col items-end">
                    <span className="text-2xl font-bold text-blue-400">{profile.defense_relevance_score.toFixed(1)}</span>
                    <span className="text-xs text-zinc-500 font-medium uppercase tracking-wider">Score</span>
                  </div>
                </div>

                {profile.bio && (
                  <p className="text-sm text-zinc-300 mb-4 line-clamp-2">{profile.bio}</p>
                )}

                <div className="flex flex-wrap gap-x-4 gap-y-2 text-xs text-zinc-400">
                  {profile.location && (
                    <div className="flex items-center gap-1.5">
                      <MapPin className="w-3.5 h-3.5" />
                      {profile.location}
                    </div>
                  )}
                  {profile.company && (
                    <div className="flex items-center gap-1.5">
                      <Briefcase className="w-3.5 h-3.5" />
                      {profile.company}
                    </div>
                  )}
                  <a 
                    href={`https://github.com/${profile.github_username}`} 
                    target="_blank" 
                    rel="noreferrer"
                    className="flex items-center gap-1.5 text-blue-400 hover:text-blue-300 ml-auto"
                  >
                    <Github className="w-3.5 h-3.5" />
                    GitHub Profile
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
              </motion.div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
