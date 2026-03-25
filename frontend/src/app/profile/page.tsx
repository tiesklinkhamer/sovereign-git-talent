"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { Terminal, MapPin, Briefcase, Link as LinkIcon, Save, Activity, ShieldAlert, Check } from "lucide-react";
import { motion } from "framer-motion";

export default function ProfilePage() {
  const { user, token, loading: authLoading } = useAuth();
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (token) {
      fetchProfile();
    }
  }, [token]);

  const fetchProfile = async () => {
    try {
      const res = await fetch("${process.env.NEXT_PUBLIC_API_URL}/profile/me", {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      setProfile(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setMessage("");
    try {
      const res = await fetch("${process.env.NEXT_PUBLIC_API_URL}/profile/me", {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          bio: profile.bio,
          location: profile.location,
          company: profile.company,
          blog: profile.blog,
          open_to_work: profile.open_to_work,
        }),
      });
      if (res.ok) {
        setMessage("Profile updated successfully");
        setTimeout(() => setMessage(""), 3000);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setSaving(false);
    }
  };

  if (authLoading || (loading && token)) {
    return (
      <div className="flex items-center justify-center p-20">
        <Activity className="w-8 h-8 text-blue-500 animate-spin" />
      </div>
    );
  }

  if (!token) {
    return (
      <div className="flex flex-col items-center justify-center p-20 glass rounded-2xl border-dashed">
        <ShieldAlert className="w-12 h-12 text-zinc-500 mb-4" />
        <h2 className="text-xl font-bold text-white mb-2">Access Restricted</h2>
        <p className="text-zinc-400">Please sign in with GitHub to manage your defense tech profile.</p>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white mb-2">My Community Identity</h1>
          <p className="text-zinc-400">Manage how you appear to the defense tech ecosystem.</p>
        </div>
        <div className="px-4 py-1.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 text-xs font-bold uppercase tracking-widest flex items-center gap-2">
          <ShieldAlert className="w-3.5 h-3.5" />
          Verified Engineer
        </div>
      </header>

      <form onSubmit={handleUpdate} className="space-y-6">
        <div className="glass p-8 rounded-3xl space-y-8 relative overflow-hidden">
          {/* Status Toggle */}
          <div className="flex items-center justify-between p-4 bg-emerald-500/5 border border-emerald-500/10 rounded-2xl">
            <div className="flex items-center gap-4">
              <div className={`p-3 rounded-xl ${profile?.open_to_work ? 'bg-emerald-500/20 text-emerald-400' : 'bg-zinc-800 text-zinc-500'}`}>
                <Briefcase className="w-6 h-6" />
              </div>
              <div>
                <h3 className="font-semibold text-white">Open to Defense Opportunities</h3>
                <p className="text-sm text-zinc-400 text-balance">Signal to VCs and defense companies that you are exploring new roles.</p>
              </div>
            </div>
            <button
              type="button"
              onClick={() => setProfile({ ...profile, open_to_work: !profile.open_to_work })}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none ring-2 ring-white/10 ${profile?.open_to_work ? 'bg-emerald-500' : 'bg-zinc-700'}`}
            >
              <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${profile?.open_to_work ? 'translate-x-6' : 'translate-x-1'}`} />
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <label className="text-xs font-bold text-zinc-500 uppercase px-1">Location</label>
              <div className="relative">
                <MapPin className="w-4 h-4 absolute left-4 top-1/2 -translate-y-1/2 text-zinc-500" />
                <input 
                  type="text" 
                  className="w-full bg-black/30 border border-white/10 rounded-xl pl-11 pr-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all font-medium"
                  value={profile?.location || ""}
                  onChange={(e) => setProfile({ ...profile, location: e.target.value })}
                  placeholder="e.g. London, UK"
                />
              </div>
            </div>
            
            <div className="space-y-2">
              <label className="text-xs font-bold text-zinc-500 uppercase px-1">Current Company</label>
              <div className="relative">
                <ShieldAlert className="w-4 h-4 absolute left-4 top-1/2 -translate-y-1/2 text-zinc-500" />
                <input 
                  type="text" 
                  className="w-full bg-black/30 border border-white/10 rounded-xl pl-11 pr-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all font-medium"
                  value={profile?.company || ""}
                  onChange={(e) => setProfile({ ...profile, company: e.target.value })}
                  placeholder="e.g. Anduril Industries"
                />
              </div>
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-xs font-bold text-zinc-500 uppercase px-1">Professional Bio</label>
            <textarea 
              rows={4}
              className="w-full bg-black/30 border border-white/10 rounded-2xl p-4 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all font-medium resize-none"
              value={profile?.bio || ""}
              onChange={(e) => setProfile({ ...profile, bio: e.target.value })}
              placeholder="Tell us about your technical expertise..."
            />
          </div>

          <div className="space-y-2">
            <label className="text-xs font-bold text-zinc-500 uppercase px-1">Personal Website / Blog</label>
            <div className="relative">
              <LinkIcon className="w-4 h-4 absolute left-4 top-1/2 -translate-y-1/2 text-zinc-500" />
              <input 
                type="text" 
                className="w-full bg-black/30 border border-white/10 rounded-xl pl-11 pr-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all font-medium"
                value={profile?.blog || ""}
                onChange={(e) => setProfile({ ...profile, blog: e.target.value })}
                placeholder="https://yourwebsite.com"
              />
            </div>
          </div>

          <div className="flex items-center justify-between pt-4 border-t border-white/5">
            <div className="flex items-center gap-3">
              <img src={`https://github.com/${user?.username}.png`} className="w-10 h-10 rounded-full border border-white/10" alt="" />
              <div>
                <p className="text-sm font-bold text-white tracking-tight flex items-center gap-2">
                  {user?.username}
                  <Terminal className="w-3.5 h-3.5 text-zinc-500" />
                </p>
                <p className="text-[10px] text-zinc-500 font-mono">ID: {user?.github_id}</p>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              {message && (
                <span className="text-sm text-emerald-400 font-medium flex items-center gap-2 animate-in fade-in slide-in-from-right-2">
                  <Check className="w-4 h-4" />
                  {message}
                </span>
              )}
              <button 
                type="submit"
                disabled={saving}
                className="px-8 py-3 rounded-full bg-blue-600 hover:bg-blue-500 text-white font-bold text-sm transition-all shadow-lg shadow-blue-500/20 flex items-center gap-2 disabled:opacity-50"
              >
                {saving ? <Activity className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                Save Changes
              </button>
            </div>
          </div>
        </div>
      </form>
    </div>
  );
}
