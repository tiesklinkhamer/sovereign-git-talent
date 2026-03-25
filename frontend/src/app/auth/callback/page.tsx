"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { Activity } from "lucide-react";

export default function CallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { setAuth } = useAuth();
  const [error, setError] = useState(false);

  useEffect(() => {
    const code = searchParams.get("code");
    if (code) {
      handleCallback(code);
    } else {
      setError(true);
    }
  }, [searchParams]);

  const handleCallback = async (code: string) => {
    try {
      const res = await fetch(`http://127.0.0.1:8000/auth/github/callback?code=${code}`);
      if (res.ok) {
        const data = await res.json();
        setAuth(data.access_token);
        router.push("/profile");
      } else {
        setError(true);
      }
    } catch (e) {
      console.error("Callback error:", e);
      setError(true);
    }
  };

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center p-20 glass rounded-2xl">
        <h2 className="text-xl font-bold text-red-400 mb-2">Authentication Failed</h2>
        <p className="text-zinc-400 mb-6">Something went wrong during the login process.</p>
        <button 
          onClick={() => router.push("/")}
          className="px-6 py-2 bg-white/5 rounded-full text-white hover:bg-white/10 transition-colors border border-white/10"
        >
          Return Home
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center p-20">
      <Activity className="w-12 h-12 text-blue-500 animate-spin mb-4" />
      <h2 className="text-xl font-medium text-white">Finalizing Authentication...</h2>
      <p className="text-zinc-400">Please wait while we set up your secure session.</p>
    </div>
  );
}
