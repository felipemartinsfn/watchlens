import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Navbar } from "@/components/Navbar";
import { Providers } from "@/components/Providers";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "WatchLens — Descubra Relógios por Imagem",
  description:
    "Plataforma de descoberta de relógios. Busque por imagem, texto ou filtros e encontre o modelo exato ou similares com score de similaridade visual.",
  keywords: ["relógios", "watch", "busca por imagem", "similaridade", "catálogo"],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR" className="dark">
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased min-h-screen bg-slate-950`}>
        <Providers>
          <Navbar />
          <main className="min-h-[calc(100vh-64px)]">{children}</main>
          <footer className="border-t border-slate-800 py-8 mt-16">
            <div className="container mx-auto px-4 text-center text-slate-500 text-sm">
              <p>WatchLens © {new Date().getFullYear()} — Descubra o relógio perfeito</p>
            </div>
          </footer>
        </Providers>
      </body>
    </html>
  );
}
