"use client";
import { useState, useCallback, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { watchesApi, filtersApi, SearchParams, ImageSearchResponse } from "@/lib/api";
import { WatchGrid } from "@/components/WatchGrid";
import { FilterSidebar } from "@/components/FilterSidebar";
import { ImageUpload } from "@/components/ImageUpload";
import { ScoreBadge } from "@/components/ScoreBadge";
import { SearchBar } from "@/components/SearchBar";
import { Camera, Search, SlidersHorizontal, X, ChevronLeft, ChevronRight } from "lucide-react";
import Image from "next/image";
import Link from "next/link";

const PLACEHOLDER = "https://images.unsplash.com/photo-1523170335258-f5ed11844a49?w=400&q=60";

function SearchPageInner() {
  const searchParams = useSearchParams();
  const router = useRouter();

  function getList(key: string): string[] {
    const val = searchParams.get(key);
    return val ? val.split(",").filter(Boolean) : [];
  }

  const q = searchParams.get("q") || undefined;
  const page = Number(searchParams.get("page") || 1);
  const selectedStyles = getList("watch_styles");
  const selectedEras = getList("eras");
  const selectedCaseMaterials = getList("case_materials");
  const selectedDialColors = getList("dial_colors");
  const selectedBezelTypes = getList("bezel_types");
  const selectedMovementTypes = getList("movement_types");
  const selectedBrandIds = getList("brand_ids");
  const diameterMin = searchParams.get("diameter_min") ? Number(searchParams.get("diameter_min")) : undefined;
  const diameterMax = searchParams.get("diameter_max") ? Number(searchParams.get("diameter_max")) : undefined;
  const yearStart = searchParams.get("year_start") ? Number(searchParams.get("year_start")) : undefined;
  const yearEnd = searchParams.get("year_end") ? Number(searchParams.get("year_end")) : undefined;

  const [mode, setMode] = useState<"text" | "image">("text");
  const [imageResult, setImageResult] = useState<ImageSearchResponse | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const { data: filterOptions } = useQuery({
    queryKey: ["filter-options"],
    queryFn: filtersApi.options,
    staleTime: 5 * 60 * 1000,
  });

  const currentParams: SearchParams = {
    q,
    brand_ids: selectedBrandIds.join(",") || undefined,
    watch_styles: selectedStyles.join(",") || undefined,
    eras: selectedEras.join(",") || undefined,
    case_materials: selectedCaseMaterials.join(",") || undefined,
    dial_colors: selectedDialColors.join(",") || undefined,
    bezel_types: selectedBezelTypes.join(",") || undefined,
    movement_types: selectedMovementTypes.join(",") || undefined,
    diameter_min: diameterMin,
    diameter_max: diameterMax,
    year_start: yearStart,
    year_end: yearEnd,
    page,
    per_page: 24,
  };

  const { data, isLoading } = useQuery({
    queryKey: ["watches", currentParams],
    queryFn: () => watchesApi.list(currentParams),
    enabled: mode === "text",
  });

  function pushParams(overrides: Record<string, string | undefined>) {
    const params = new URLSearchParams(searchParams.toString());
    Object.entries(overrides).forEach(([key, val]) => {
      if (val === undefined || val === "") params.delete(key);
      else params.set(key, val);
    });
    router.push(`/search?${params.toString()}`);
  }

  function handleFilterChange(key: string, values: string[]) {
    pushParams({ [key]: values.join(",") || undefined, page: "1" });
  }

  function handleDiameterChange(range: [number, number]) {
    pushParams({
      diameter_min: range[0] ? String(range[0]) : undefined,
      diameter_max: range[1] ? String(range[1]) : undefined,
      page: "1",
    });
  }

  function handleYearChange(range: [number, number]) {
    pushParams({
      year_start: range[0] ? String(range[0]) : undefined,
      year_end: range[1] ? String(range[1]) : undefined,
      page: "1",
    });
  }

  function clearFilters() {
    router.push(q ? `/search?q=${encodeURIComponent(q)}` : "/search");
  }

  const handleImageResult = useCallback((result: ImageSearchResponse) => {
    setImageResult(result);
    setMode("image");
  }, []);

  const hasActiveFilters = !!(
    selectedStyles.length || selectedEras.length || selectedCaseMaterials.length ||
    selectedDialColors.length || selectedBezelTypes.length || selectedMovementTypes.length ||
    selectedBrandIds.length || diameterMin || diameterMax
  );

  const totalPages = data?.total_pages ?? 1;
  const total = data?.total ?? 0;

  const selectedMap = {
    watch_styles: selectedStyles,
    eras: selectedEras,
    case_materials: selectedCaseMaterials,
    dial_colors: selectedDialColors,
    bezel_types: selectedBezelTypes,
    movement_types: selectedMovementTypes,
    brand_ids: selectedBrandIds,
  };

  const diameterRangeValue: [number, number] = [
    diameterMin ?? (filterOptions?.diameter_range.min ?? 30),
    diameterMax ?? (filterOptions?.diameter_range.max ?? 50),
  ];

  const yearRangeValue: [number, number] = [
    yearStart ?? (filterOptions?.year_range.min ?? 1950),
    yearEnd ?? (filterOptions?.year_range.max ?? new Date().getFullYear()),
  ];

  return (
    <div className="container mx-auto px-4 py-8">
      {/* ── Header ── */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white mb-4">Explorar Catálogo</h1>

        <div className="flex items-center gap-2 mb-4">
          <button
            onClick={() => setMode("text")}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all ${
              mode === "text" ? "bg-blue-600 text-white" : "bg-slate-800 text-slate-400 hover:text-white"
            }`}
          >
            <Search className="w-4 h-4" />
            Texto &amp; Filtros
          </button>
          <button
            onClick={() => setMode("image")}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all ${
              mode === "image" ? "bg-blue-600 text-white" : "bg-slate-800 text-slate-400 hover:text-white"
            }`}
          >
            <Camera className="w-4 h-4" />
            Busca por Imagem
          </button>
        </div>

        {mode === "text" && (
          <div className="flex items-center gap-3">
            <div className="flex-1 max-w-lg">
              <SearchBar />
            </div>
            <button
              onClick={() => setSidebarOpen(true)}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 transition-all text-sm font-medium lg:hidden"
            >
              <SlidersHorizontal className="w-4 h-4" />
              Filtros
              {hasActiveFilters && <span className="w-2 h-2 rounded-full bg-blue-500" />}
            </button>
            {hasActiveFilters && (
              <button
                onClick={clearFilters}
                className="hidden lg:flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-800 text-slate-400 hover:text-white text-sm transition-all"
              >
                <X className="w-3.5 h-3.5" />
                Limpar filtros
              </button>
            )}
          </div>
        )}
      </div>

      {/* ── Image mode ── */}
      {mode === "image" && (
        <div className="max-w-md mx-auto mb-10">
          <ImageUpload onResult={handleImageResult} />
        </div>
      )}

      {mode === "image" && imageResult && (
        <div className="space-y-8">
          {imageResult.best_match && (
            <div>
              <h2 className="text-lg font-semibold text-white mb-3">Melhor correspondência</h2>
              <Link
                href={`/watch/${imageResult.best_match.watch.slug}`}
                className="inline-flex items-center gap-4 p-4 rounded-2xl border border-emerald-500/30 bg-emerald-500/5 hover:bg-emerald-500/10 transition-all"
              >
                <div className="relative w-16 h-16 rounded-xl overflow-hidden bg-slate-800 shrink-0">
                  <Image
                    src={imageResult.best_match.watch.thumbnail_url || PLACEHOLDER}
                    alt={imageResult.best_match.watch.name}
                    fill className="object-cover"
                  />
                </div>
                <div>
                  <p className="text-xs text-blue-400">{imageResult.best_match.watch.brand_name}</p>
                  <p className="text-white font-semibold">{imageResult.best_match.watch.name}</p>
                  <ScoreBadge score={imageResult.best_match.score} />
                </div>
              </Link>
            </div>
          )}
          {imageResult.similar_watches.length > 0 && (
            <div>
              <h2 className="text-lg font-semibold text-white mb-4">Visualmente similares</h2>
              <WatchGrid
                watches={imageResult.similar_watches.map((s) => ({ ...s.watch, similarity_score: s.score }))}
                showScores cols={4}
              />
            </div>
          )}
          {!imageResult.best_match && imageResult.similar_watches.length === 0 && (
            <p className="text-center py-16 text-slate-500">
              Nenhuma correspondência encontrada. Tente com outra imagem.
            </p>
          )}
        </div>
      )}

      {/* ── Text mode ── */}
      {mode === "text" && (
        <div className="flex gap-6">
          {filterOptions && (
            <div className="hidden lg:block">
              <FilterSidebar
                options={filterOptions}
                selected={selectedMap}
                diameterRange={diameterRangeValue}
                yearRange={yearRangeValue}
                onChange={handleFilterChange}
                onDiameterChange={handleDiameterChange}
                onYearChange={handleYearChange}
                onReset={clearFilters}
              />
            </div>
          )}

          {sidebarOpen && filterOptions && (
            <div className="fixed inset-0 z-50 flex lg:hidden">
              <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setSidebarOpen(false)} />
              <div className="relative ml-auto w-80 h-full bg-slate-900 border-l border-slate-800 overflow-y-auto p-4">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="font-semibold text-white">Filtros</h2>
                  <button onClick={() => setSidebarOpen(false)}>
                    <X className="w-5 h-5 text-slate-400" />
                  </button>
                </div>
                <FilterSidebar
                  options={filterOptions}
                  selected={selectedMap}
                  diameterRange={diameterRangeValue}
                  yearRange={yearRangeValue}
                  onChange={handleFilterChange}
                  onDiameterChange={handleDiameterChange}
                  onYearChange={handleYearChange}
                  onReset={clearFilters}
                />
              </div>
            </div>
          )}

          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between mb-4">
              <p className="text-sm text-slate-400">
                {isLoading ? "Carregando..." : `${total.toLocaleString()} resultado${total !== 1 ? "s" : ""}`}
              </p>
              {hasActiveFilters && (
                <button onClick={clearFilters} className="flex items-center gap-1.5 text-sm text-slate-400 hover:text-white transition-colors">
                  <X className="w-3.5 h-3.5" /> Limpar filtros
                </button>
              )}
            </div>

            <WatchGrid watches={data?.results ?? []} loading={isLoading} cols={3} />

            {totalPages > 1 && (
              <div className="flex items-center justify-center gap-2 mt-10">
                <button
                  disabled={page <= 1}
                  onClick={() => pushParams({ page: String(page - 1) })}
                  className="flex items-center gap-1 px-4 py-2 rounded-xl bg-slate-800 text-slate-300 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed transition-all text-sm"
                >
                  <ChevronLeft className="w-4 h-4" /> Anterior
                </button>
                <div className="flex gap-1">
                  {Array.from({ length: Math.min(totalPages, 7) }, (_, i) => {
                    let pn: number;
                    if (totalPages <= 7) pn = i + 1;
                    else if (page <= 4) pn = i + 1;
                    else if (page >= totalPages - 3) pn = totalPages - 6 + i;
                    else pn = page - 3 + i;
                    return (
                      <button
                        key={pn}
                        onClick={() => pushParams({ page: String(pn) })}
                        className={`w-9 h-9 rounded-lg text-sm font-medium transition-all ${
                          pn === page ? "bg-blue-600 text-white" : "bg-slate-800 text-slate-400 hover:text-white"
                        }`}
                      >
                        {pn}
                      </button>
                    );
                  })}
                </div>
                <button
                  disabled={page >= totalPages}
                  onClick={() => pushParams({ page: String(page + 1) })}
                  className="flex items-center gap-1 px-4 py-2 rounded-xl bg-slate-800 text-slate-300 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed transition-all text-sm"
                >
                  Próxima <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense
      fallback={
        <div className="container mx-auto px-4 py-8">
          <div className="animate-pulse space-y-4">
            <div className="h-8 bg-slate-800 rounded-xl w-48" />
            <div className="grid grid-cols-3 gap-4">
              {Array.from({ length: 9 }).map((_, i) => (
                <div key={i} className="aspect-[3/4] bg-slate-800 rounded-2xl" />
              ))}
            </div>
          </div>
        </div>
      }
    >
      <SearchPageInner />
    </Suspense>
  );
}
