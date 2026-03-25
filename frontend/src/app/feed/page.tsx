"use client";

import { useEffect, useState } from "react";
import { Activity, ShieldAlert, GitCommit, GitBranch, Github, ExternalLink } from "lucide-react";
import { motion } from "framer-motion";

export default function FeedPage() {
  const [feed, setFeed] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchFeed();
  }, []);

  const fetchFeed = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/feed");
      const data = await res.json();
      setFeed(data.feed || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-500 max-w-4xl mx-auto">
      <header>
        <h1 className="text-3xl font-bold tracking-tight text-white mb-2 flex items-center gap-3">
          <Activity className="w-8 h-8 text-blue-500" />
          Signal Feed
        </h1>
        <p className="text-zinc-400">Real-time anomalous dual-use tech activities detected by Claude.</p>
      </header>

      {loading ? (
        <div className="flex items-center justify-center p-20">
          <Activity className="w-8 h-8 text-blue-500 animate-spin" />
        </div>
      ) : (
        <div className="space-y-4">
          {feed.length === 0 ? (
            <div className="text-center p-12 glass rounded-2xl border-dashed">
              <p className="text-zinc-400">No anomalous signals detected yet.</p>
            </div>
          ) : (
            feed.map((item, i) => (
              <motion.div 
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.05 }}
                key={item.log_id} 
                className="glass p-6 rounded-2xl flex gap-6 relative overflow-hidden group hover:border-blue-500/50 transition-colors"
              >
                {/* Accent line */}
                <div className="absolute left-0 top-0 bottom-0 w-1 bg-red-500/50" />
                
                <div className="shrink-0 flex flex-col items-center">
                  <div className="w-10 h-10 rounded-full bg-red-500/10 border border-red-500/20 flex items-center justify-center text-red-400 mb-2">
                    <ShieldAlert className="w-5 h-5" />
                  </div>
                  <div className="w-px h-full bg-white/5" />
                </div>
                
                <div className="flex-1 pb-2">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-3">
                      <img 
                        src={`https://github.com/${item.username}.png`} 
                        alt={item.username}
                        className="w-8 h-8 rounded-full border border-white/10"
                      />
                      <div>
                        <a href={`https://github.com/${item.username}`} target="_blank" rel="noreferrer" className="text-white font-medium hover:text-blue-400 transition-colors flex items-center gap-1.5">
                          {item.username}
                        </a>
                        <p className="text-xs text-zinc-500 flex items-center gap-1.5 uppercase font-medium tracking-wide">
                          {item.domain || "Unknown Domain"} 
                          &middot; 
                          {new Date(item.analyzed_at).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                    
                    <a 
                      href={`https://github.com/${item.username}`}
                      target="_blank"
                      rel="noreferrer"
                      className="px-3 py-1.5 rounded-full bg-white/5 hover:bg-white/10 text-xs text-white border border-white/5 transition-colors flex items-center gap-2"
                    >
                      View Target <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                  
                  <div className="bg-black/30 border border-white/5 rounded-xl p-4 mb-4">
                    <p className="text-sm text-zinc-300 leading-relaxed">
                      {item.summary}
                    </p>
                  </div>
                  
                  <div className="flex items-center gap-4 text-xs font-medium text-zinc-500">
                    <span className="flex items-center gap-1.5 bg-white/5 px-2.5 py-1 rounded-md border border-white/5">
                      {item.event_type === "PushEvent" && <GitCommit className="w-3.5 h-3.5" />}
                      {item.event_type === "CreateEvent" && <GitBranch className="w-3.5 h-3.5" />}
                      {item.event_type === "PullRequestEvent" && <Github className="w-3.5 h-3.5" />}
                      {item.event_type}
                    </span>
                    <span className="flex items-center gap-1.5 text-zinc-400">
                      in <span className="text-blue-400">{item.repo_name || "Unknown Repo"}</span>
                    </span>
                  </div>
                </div>
              </motion.div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
