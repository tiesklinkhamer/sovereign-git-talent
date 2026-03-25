"use client";

import Link from "next/link";
import { Search, Activity, ShieldAlert, User, LogOut, Terminal, Target } from "lucide-react";
import { useAuth } from "@/context/AuthContext";

export default function Sidebar() {
  const { user, login, logout, loading } = useAuth();

  return (
    <aside className="w-64 border-r border-white/10 bg-black/40 backdrop-blur-sm p-6 flex flex-col gap-8 hidden md:flex shrink-0">
      <div className="flex items-center gap-3 text-white font-bold text-xl tracking-tight">
        <ShieldAlert className="w-6 h-6 text-blue-500" />
        Talent Sonar
      </div>
      
      <nav className="flex flex-col gap-2 flex-grow">
        <Link href="/" className="flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium text-zinc-400 hover:text-white hover:bg-white/5 transition-all">
          <Search className="w-5 h-5" />
          Talent Search
        </Link>
        <Link href="/feed" className="flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium text-zinc-400 hover:text-white hover:bg-white/5 transition-all">
          <Activity className="w-5 h-5" />
          Signal Feed
        </Link>
        <Link href="/matchmaking" className="flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium text-zinc-400 hover:text-white hover:bg-white/5 transition-all">
          <Target className="w-5 h-5" />
          Matchmaking
        </Link>
        {user && (
          <Link href="/profile" className="flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium text-zinc-400 hover:text-white hover:bg-white/5 transition-all">
            <User className="w-5 h-5" />
            My Profile
          </Link>
        )}
      </nav>

      <div className="mt-auto pt-6 border-t border-white/10">
        {loading ? (
          <div className="w-full h-10 bg-white/5 animate-pulse rounded-full" />
        ) : user ? (
          <div className="space-y-4">
            <div className="flex items-center gap-3 px-2">
              <img 
                src={`https://github.com/${user.username}.png`} 
                alt={user.username}
                className="w-8 h-8 rounded-full border border-white/10"
              />
              <span className="text-sm font-medium text-zinc-300 truncate">{user.username}</span>
            </div>
            <button 
              onClick={logout}
              className="w-full flex items-center justify-center gap-2 py-2.5 rounded-full bg-white/5 text-zinc-400 hover:text-white hover:bg-white/10 text-xs font-semibold transition-all border border-white/5"
            >
              <LogOut className="w-3.5 h-3.5" />
              Sign Out
            </button>
          </div>
        ) : (
          <button 
            onClick={login}
            className="w-full flex items-center justify-center gap-2 py-2.5 rounded-full bg-white text-black hover:bg-zinc-200 text-xs font-bold transition-all shadow-lg"
          >
            <Terminal className="w-4 h-4" />
            Sign in with GitHub
          </button>
        )}
      </div>
    </aside>
  );
}
