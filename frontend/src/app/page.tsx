"use client";
import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import Image from "next/image";
import Link from "next/link";
import { watchesApi, ImageSearchResponse, WatchCard } from "@/lib/api";
import { SearchBar } from "@/components/SearchBar";
import { ImageUpload } from "@/components/ImageUpload";
import { WatchGrid } from "@/components/WatchGrid";
import { ScoreBadge } from "@/components/ScoreBadge";
import { WatchCard as WatchCardComponent } from "@/components/WatchCard";
import { formatStyle, getStyleIcon } from "@/lib/utils";
import { Camera, Search, Layers, ArrowRight, Sparkles } from "lucide-react";

const STYLE_CATEGORIES = [
  { key: "diver", label: "Mergulho", color: "from-blue-600 to-cyan-500" },
  { key: "dress", label: "Social", color: "from-amber-600 to-yellow-500" },
  { key: "pilot", label: "Piloto", color: "from-slate-600 to-slate-400" },
  { key: "racing", label: "Racing", color: "from-red-600 to-orange-500" },
  { key: "sport", label: "Esportivo", color: "from-green-600 to-emerald-500" },
  { key: "field", label: "Campo", color: "from-stone-600 to-stone-400" },
];

const PLACEHOLDER = "https://images.unsplash.com/photo-1523170335258-f5ed11844a49?w=400&q=60";

export default function HomePage() {
  const router = useRouter();
  const [imageResult, setImageResult] = useState<ImageSearchResponse | null>(null);

  const { data: featured = [] } = useQuery({
    queryKey: ["featured"],
    queryFn: () => watchesApi.featured(8),
  });

  const handleImageResult = useCallback((result: ImageSearchResponse) => {
    setImageResult(result);
    // Scroll to results
    setTimeout(() => {
      document.getElementById("image-results")?.scrollIntoView({ behavior: "smooth" });
    }, 100);
  }, []);

  return (
    <div className="min-h-screen">
      {/* ── HERO ── */}
      <section className="relative overflow-hidden bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 pt-16 pb-20">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-blue-900/20 via-transparent to-transparent" />
        <div className="container mx-auto px-4 relative">
          <div className="max-w-2xl mx-auto text-center mb-10">
            <div className="inline-flex items-center gap-2 text-sm text-blue-400 bg-blue-400/10 border border-blue-400/20 rounded-full px-4 py-1.5 mb-6">
              <Sparkles className="w-3.5 h-3.5" />
              Busca visual por IA
            </div>
            <h1 className="text-4xl sm:text-5xl font-bold text-white mb-4 leading-tight">
              Descubra relógios pelo<br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-cyan-400">
                que você vê
              </span>
            </h1>
            <p className="text-slate-400 text-lg mb-8">
              Envie uma foto, descreva em palavras ou use filtros para encontrar o modelo exato ou os mais similares.
            </p>
            <div className="max-w-lg mx-auto">
              <SearchBar />
            </div>
          </div>

          {/* Feature pills */}
          <div className="flex flex-wrap justify-center gap-3 mt-6">
            {[
              { icon: <Camera className="w-3.5 h-3.5" />, label: "Busca por imagem" },
              { icon: <Search className="w-3.5 h-3.5" />, label: "Busca por texto" },
              { icon: <Layers className="w-3.5 h-3.5" />, label: "Filtros avançados" },
            ].map((f) => (
              <div key={f.label} className="flex items-center gap-1.5 text-sm text-slate-400 bg-slate-800/50 rounded-full px-3 py-1.5">
                {f.icon}
                {f.label}
              </div>
            ))}
          </div>
        </div>
      </section>

      <div className="container mx-auto px-4 py-12 space-y-16">
        {/* ── IMAGE SEARCH ── */}
        <section>
          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold text-white mb-2">Busca por Imagem</h2>
            <p className="text-slate-400">Envie uma foto de relógio e encontraremos correspondências visuais</p>
          </div>
          <div className="max-w-md mx-auto">
            <ImageUpload onResult={handleImageResult} />
          </div>
        </section>

        {/* ── IMAGE RESULTS ── */}
        {imageResult && (
          <section id="image-results">
            <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
              <Camera className="w-6 h-6 text-blue-400" />
              Resultados da Busca Visual
            </h2>

            {/* Best match */}
            {imageResult.best_match && (
              <div className="mb-8">
                <p className="text-sm text-slate-400 mb-3">Melhor correspondência</p>
                <Link href={`/watch/${imageResult.best_match.watch.slug}`}
                  className="flex items-center gap-4 p-4 rounded-2xl border border-emerald-500/30 bg-emerald-500/5 hover:bg-emerald-500/10 transition-all max-w-sm">
                  <div className="relative w-20 h-20 rounded-xl overflow-hidden bg-slate-800 shrink-0">
                    <Image
                      src={imageResult.best_match.watch.thumbnail_url || PLACEHOLDER}
                      alt={imageResult.best_match.watch.name}
                      fill className="object-cover"
                    />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-blue-400 font-medium">{imageResult.best_match.watch.brand_name}</p>
                    <p className="text-white font-semibold truncate">{imageResult.best_match.watch.name}</p>
                    <ScoreBadge score={imageResult.best_match.score} />
                  </div>
                </Link>
              </div>
            )}

            {/* Similar watches */}
            {imageResult.similar_watches.length > 0 && (
              <div>
                <p className="text-sm text-slate-400 mb-4">Visualmente similares</p>
                <WatchGrid
                  watches={imageResult.similar_watches.map((s) => ({
                    ...s.watch,
                    similarity_score: s.score,
                  }))}
                  showScores
                  cols={4}
                />
              </div>
            )}

            {!imageResult.best_match && imageResult.similar_watches.length === 0 && (
              <p className="text-slate-500 text-center py-8">
                Nenhuma correspondência encontrada. Tente com outra imagem ou expanda o catálogo.
              </p>
            )}
          </section>
        )}

        {/* ── STYLE CATEGORIES ── */}
        <section>
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-white">Explorar por Estilo</h2>
            <Link href="/search" className="text-sm text-blue-400 hover:text-blue-300 flex items-center gap-1">
              Ver todos <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            {STYLE_CATEGORIES.map((cat) => (
              <Link
                key={cat.key}
                href={`/search?watch_styles=${cat.key}`}
                className="group relative overflow-hidden rounded-xl p-4 text-center border border-slate-800 bg-slate-900 hover:border-slate-600 transition-all hover:scale-105"
              >
                <div className={`absolute inset-0 bg-gradient-to-br ${cat.color} opacity-0 group-hover:opacity-10 transition-opacity`} />
                <div className="text-3xl mb-2">{getStyleIcon(cat.key)}</div>
                <p className="text-sm font-medium text-slate-300 group-hover:text-white transition-colors">
                  {cat.label}
                </p>
              </Link>
            ))}
          </div>
        </section>

        {/* ── FEATURED ── */}
        {featured.length > 0 && (
          <section>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-white">Destaque do Catálogo</h2>
              <Link href="/search" className="text-sm text-blue-400 hover:text-blue-300 flex items-center gap-1">
                Ver todos <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
            <WatchGrid watches={featured} cols={4} />
          </section>
        )}
      </div>
    </div>
  );
}
