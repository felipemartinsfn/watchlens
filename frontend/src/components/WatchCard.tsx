"use client";
import Image from "next/image";
import Link from "next/link";
import { WatchCard as WatchCardType } from "@/lib/api";
import { ScoreBadge } from "./ScoreBadge";
import { formatStyle, formatMovement, formatYearRange } from "@/lib/utils";

interface WatchCardProps {
  watch: WatchCardType;
  showScore?: boolean;
}

const PLACEHOLDER = "https://images.unsplash.com/photo-1523170335258-f5ed11844a49?w=400&q=60";

export function WatchCard({ watch, showScore = false }: WatchCardProps) {
  const imgSrc = watch.thumbnail_url || watch.primary_image_url || PLACEHOLDER;

  return (
    <Link href={`/watch/${watch.slug}`} className="group block">
      <div className="rounded-2xl border border-slate-800 bg-slate-900 overflow-hidden hover:border-blue-500/50 hover:bg-slate-800/80 transition-all duration-200 hover:shadow-xl hover:shadow-blue-500/5">
        {/* Image */}
        <div className="relative aspect-square bg-slate-800 overflow-hidden">
          <Image
            src={imgSrc}
            alt={watch.name}
            fill
            className="object-cover group-hover:scale-105 transition-transform duration-300"
            sizes="(max-width: 640px) 50vw, (max-width: 1024px) 33vw, 25vw"
            onError={(e) => { (e.target as HTMLImageElement).src = PLACEHOLDER; }}
          />
          {/* Score overlay */}
          {showScore && watch.similarity_score != null && (
            <div className="absolute top-2 right-2">
              <ScoreBadge score={watch.similarity_score} size="sm" />
            </div>
          )}
          {/* Style badge */}
          {watch.watch_style && (
            <div className="absolute bottom-2 left-2">
              <span className="text-xs px-2 py-0.5 rounded-full bg-black/60 backdrop-blur-sm text-white border border-white/10">
                {formatStyle(watch.watch_style)}
              </span>
            </div>
          )}
        </div>

        {/* Info */}
        <div className="p-3">
          <p className="text-xs text-blue-400 font-medium truncate mb-0.5">
            {watch.brand_name}
          </p>
          <h3 className="text-sm font-semibold text-white leading-snug line-clamp-2 mb-1">
            {watch.name}
          </h3>
          {watch.reference_number && (
            <p className="text-xs text-slate-500 font-mono mb-2">{watch.reference_number}</p>
          )}
          <div className="flex items-center gap-2 flex-wrap">
            {watch.case_diameter_mm && (
              <span className="text-xs text-slate-400">{watch.case_diameter_mm}mm</span>
            )}
            {watch.movement_type && (
              <span className="text-xs text-slate-500">· {formatMovement(watch.movement_type)}</span>
            )}
          </div>
          {(watch.production_year_start) && (
            <p className="text-xs text-slate-600 mt-1">
              {formatYearRange(watch.production_year_start, watch.production_year_end)}
            </p>
          )}
        </div>
      </div>
    </Link>
  );
}
