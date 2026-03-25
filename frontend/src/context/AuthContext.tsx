"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

interface User {
  github_id: string;
  username: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: () => void;
  logout: () => void;
  setAuth: (token: string) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const savedToken = localStorage.getItem("sonar_token");
    if (savedToken) {
      setToken(savedToken);
      fetchUser(savedToken);
    } else {
      setLoading(false);
    }
  }, []);

  const fetchUser = async (t: string) => {
    try {
      const res = await fetch("${process.env.NEXT_PUBLIC_API_URL}/profile/me", {
        headers: { Authorization: `Bearer ${t}` },
      });
      if (res.ok) {
        const data = await res.json();
        setUser({ github_id: data.github_id, username: data.github_username });
      } else {
        logout();
      }
    } catch (e) {
      console.error("Auth error:", e);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async () => {
    const res = await fetch("${process.env.NEXT_PUBLIC_API_URL}/auth/github/login");
    const data = await res.json();
    if (data.url) {
      window.location.href = data.url;
    }
  };

  const logout = () => {
    localStorage.removeItem("sonar_token");
    setToken(null);
    setUser(null);
    router.push("/");
  };

  const setAuth = (t: string) => {
    localStorage.setItem("sonar_token", t);
    setToken(t);
    fetchUser(t);
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout, setAuth }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
