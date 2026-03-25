import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/context/AuthContext";
import Sidebar from "@/components/Sidebar";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Talent Sonar - Sovereign Git",
  description: "Advanced defense tech talent discovery engine.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} flex min-h-screen antialiased selection:bg-blue-500/30`}>
        <AuthProvider>
          <Sidebar />
          {/* Main Content */}
          <main className="flex-1 p-6 md:p-10 max-w-7xl mx-auto w-full">
            {children}
          </main>
        </AuthProvider>
      </body>
    </html>
  );
}
