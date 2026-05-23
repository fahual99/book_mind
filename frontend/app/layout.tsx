import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";
import Navbar from "@/components/Navbar";
import { Analytics } from "@vercel/analytics/next";

export const metadata: Metadata = {
  title: "BookMind AI — Intelligent Book Recommendations",
  description:
    "AI-powered book recommendation system using FAISS, TF-IDF, and hybrid collaborative filtering. Discover your next favorite read.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Playfair+Display:ital,wght@0,400;0,700;1,400&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
        {/* Ambient Background */}
        <div className="ambient-bg">
          <div className="orb orb-1" />
          <div className="orb orb-2" />
          <div className="orb orb-3" />
        </div>

        <Providers>
          <Navbar />
          <main className="relative z-10 min-h-screen">{children}</main>
        </Providers>
        <Analytics />
      </body>
    </html>
  );
}
