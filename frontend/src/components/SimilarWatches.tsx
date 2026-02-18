"use client";
import { useQuery } from "@tanstack/react-query";
import { watchesApi, SimilarWatch } from "@/lib/api";
import { WatchCard } from "./WatchCard";
import { ScoreBadge } from "./ScoreBadge";
import Link from "next/link";
import Image from "next/image";
import { formatStyle, formatYearRange } from "@/lib/utils";
import { Loader2 } from "lucide-react";

const PLACEHOLDER = "https://images.unsplash.com/photo-1523170335258-f5ed11844a49?w=400&q=60";

interface SimilarWatchesProps {
  slug: string;
}

export function SimilarWatches({ slug }: SimilarWatchesProps) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["similar", slug],
    queryFn: () => watchesApi.similar(slug, 12),
    enabled: !!slug,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-6 h-6 text-blue-400 animate-spin" />
      </div>
    );
  }

  if (isError || !data?.length) {
    return (
      <p className="text-slate-500 text-sm py-6">
        Nenhum relógio similar encontrado no catálogo ainda.
      </p>
    );
  }

  return (
    <div className="space-y-3">
      {data.map((item: SimilarWatch) => (
        <Link
          key={item.watch.id}
          href={`/watch/${item.watch.slug}`}
          className="flex items-center gap-4 p-3 rounded-xl border border-slate-800 bg-slate-900 hover:border-blue-500/40 hover:bg-slate-800/80 transition-all group"
        >
          <div className="relative w-16 h-16 rounded-lg overflow-hidden bg-slate-800 shrink-0">
            <Image
              src={item.watch.thumbnail_url || item.watch.primary_image_url || PLACEHOLDER}
              alt={item.watch.name}
              fill
              className="object-cover group-hover:scale-105 transition-transform duration-200"
            />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs text-blue-400 font-medium truncate">{item.watch.brand_name}</p>
            <p className="text-sm font-semibold text-white truncate">{item.watch.name}</p>
            <p className="text-xs text-slate-500">
              {formatStyle(item.watch.watch_style)} · {formatYearRange(item.watch.production_year_start, item.watch.production_year_end)}
            </p>
          </div>
          <ScoreBadge score={item.score} size="sm" />
        </Link>
      ))}
    </div>
  );
}
