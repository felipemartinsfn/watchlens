"use client";
import { useState } from "react";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import Image from "next/image";
import Link from "next/link";
import { watchesApi } from "@/lib/api";
import { SimilarWatches } from "@/components/SimilarWatches";
import {
  formatEra,
  formatStyle,
  formatMovement,
  formatYearRange,
  getStyleIcon,
} from "@/lib/utils";
import {
  ArrowLeft,
  Calendar,
  Ruler,
  Layers,
  Gauge,
  Droplets,
  Zap,
  Award,
  Tag,
} from "lucide-react";

const PLACEHOLDER = "https://images.unsplash.com/photo-1523170335258-f5ed11844a49?w=800&q=80";

function SpecRow({ label, value }: { label: string; value?: string | number | boolean | null }) {
  if (value === undefined || value === null || value === "" || value === false) return null;
  const display = typeof value === "boolean" ? (value ? "Sim" : "Não") : String(value);
  return (
    <div className="flex justify-between items-center py-2 border-b border-slate-800 last:border-0">
      <span className="text-slate-400 text-sm">{label}</span>
      <span className="text-slate-200 text-sm font-medium text-right max-w-[60%]">{display}</span>
    </div>
  );
}

function SpecCard({ title, icon, children }: { title: string; icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
      <div className="flex items-center gap-2 mb-4">
        <div className="text-blue-400">{icon}</div>
        <h3 className="font-semibold text-white text-sm uppercase tracking-wider">{title}</h3>
      </div>
      {children}
    </div>
  );
}

export default function WatchDetailPage() {
  const params = useParams<{ slug: string }>();
  const slug = params?.slug ?? "";

  const { data: watch, isLoading, isError } = useQuery({
    queryKey: ["watch", slug],
    queryFn: () => watchesApi.get(slug),
    enabled: !!slug,
  });

  const [activeImage, setActiveImage] = useState(0);

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-10">
        <div className="animate-pulse space-y-6">
          <div className="h-6 bg-slate-800 rounded w-48" />
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div className="aspect-square bg-slate-800 rounded-3xl" />
            <div className="space-y-4">
              <div className="h-8 bg-slate-800 rounded w-3/4" />
              <div className="h-5 bg-slate-800 rounded w-1/2" />
              <div className="grid grid-cols-2 gap-3">
                {Array.from({ length: 4 }).map((_, i) => (
                  <div key={i} className="h-32 bg-slate-800 rounded-2xl" />
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (isError || !watch) {
    return (
      <div className="container mx-auto px-4 py-20 text-center">
        <p className="text-2xl text-slate-400 mb-4">Relógio não encontrado</p>
        <Link href="/search" className="text-blue-400 hover:underline">
          Voltar à busca
        </Link>
      </div>
    );
  }

  const allImages = watch.images?.length
    ? watch.images
    : [{ id: 0, url: PLACEHOLDER, is_primary: true }];

  const activeUrl = allImages[activeImage]?.url || PLACEHOLDER;

  const complications = watch.dial_complications ?? [];

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      {/* Back */}
      <Link
        href="/search"
        className="inline-flex items-center gap-2 text-slate-400 hover:text-white transition-colors mb-6 text-sm"
      >
        <ArrowLeft className="w-4 h-4" />
        Voltar à busca
      </Link>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-10 mb-16">
        {/* ── Images ── */}
        <div className="space-y-3">
          {/* Main image */}
          <div className="relative aspect-square rounded-3xl overflow-hidden bg-slate-900 border border-slate-800">
            <Image
              src={activeUrl}
              alt={watch.name}
              fill
              className="object-contain p-6"
              priority
            />
            {watch.watch_style && (
              <div className="absolute top-4 left-4 flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-black/60 backdrop-blur-sm text-sm">
                <span>{getStyleIcon(watch.watch_style)}</span>
                <span className="text-slate-300">{formatStyle(watch.watch_style)}</span>
              </div>
            )}
            {watch.is_limited_edition && (
              <div className="absolute top-4 right-4 flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-amber-500/20 border border-amber-500/30 text-amber-400 text-xs font-medium">
                <Award className="w-3.5 h-3.5" />
                Edição Limitada
                {watch.limited_edition_count && ` · ${watch.limited_edition_count.toLocaleString()} unid.`}
              </div>
            )}
          </div>

          {/* Thumbnails */}
          {allImages.length > 1 && (
            <div className="flex gap-2 overflow-x-auto scrollbar-hide">
              {allImages.map((img, idx) => (
                <button
                  key={img.id}
                  onClick={() => setActiveImage(idx)}
                  className={`relative w-16 h-16 rounded-xl overflow-hidden shrink-0 border-2 transition-all ${
                    idx === activeImage
                      ? "border-blue-500"
                      : "border-slate-700 hover:border-slate-500"
                  }`}
                >
                  <Image src={img.url} alt="" fill className="object-cover" />
                </button>
              ))}
            </div>
          )}
        </div>

        {/* ── Header info ── */}
        <div className="space-y-6">
          <div>
            {watch.brand_name && (
              <Link
                href={`/search?q=${encodeURIComponent(watch.brand_name)}`}
                className="inline-block text-blue-400 text-sm font-medium mb-1 hover:text-blue-300 transition-colors"
              >
                {watch.brand_name}
              </Link>
            )}
            <h1 className="text-3xl font-bold text-white leading-tight">{watch.name}</h1>
            {watch.collection_name && (
              <p className="text-slate-400 text-sm mt-1">Coleção {watch.collection_name}</p>
            )}
            {watch.reference_number && (
              <p className="text-slate-500 text-sm font-mono mt-1">Ref. {watch.reference_number}</p>
            )}
          </div>

          {/* Quick stats */}
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 text-center">
              <Calendar className="w-5 h-5 text-blue-400 mx-auto mb-1" />
              <p className="text-xs text-slate-500 mb-0.5">Produção</p>
              <p className="text-white font-semibold text-sm">
                {formatYearRange(watch.production_year_start, watch.production_year_end)}
              </p>
            </div>
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 text-center">
              <Ruler className="w-5 h-5 text-blue-400 mx-auto mb-1" />
              <p className="text-xs text-slate-500 mb-0.5">Diâmetro</p>
              <p className="text-white font-semibold text-sm">
                {watch.case_diameter_mm ? `${watch.case_diameter_mm} mm` : "—"}
              </p>
            </div>
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 text-center">
              <Layers className="w-5 h-5 text-blue-400 mx-auto mb-1" />
              <p className="text-xs text-slate-500 mb-0.5">Era</p>
              <p className="text-white font-semibold text-sm">{formatEra(watch.era)}</p>
            </div>
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 text-center">
              <Gauge className="w-5 h-5 text-blue-400 mx-auto mb-1" />
              <p className="text-xs text-slate-500 mb-0.5">Movimento</p>
              <p className="text-white font-semibold text-sm">{formatMovement(watch.movement_type)}</p>
            </div>
          </div>

          {/* Description */}
          {watch.description && (
            <div className="prose prose-invert prose-sm max-w-none">
              <p className="text-slate-300 leading-relaxed">{watch.description}</p>
            </div>
          )}

          {/* Tags */}
          {watch.tags?.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Tag className="w-4 h-4 text-slate-500" />
                <span className="text-xs text-slate-500 uppercase tracking-wider">Tags</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {watch.tags.map((t) => (
                  <span
                    key={t.id}
                    className="text-xs px-2.5 py-1 rounded-full bg-slate-800 text-slate-400 border border-slate-700"
                  >
                    {t.tag}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ── Specs grid ── */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 mb-16">
        {/* Case */}
        <SpecCard title="Caixa" icon={<Layers className="w-4 h-4" />}>
          <SpecRow label="Material" value={watch.case_material} />
          <SpecRow label="Formato" value={watch.case_shape} />
          <SpecRow label="Diâmetro" value={watch.case_diameter_mm ? `${watch.case_diameter_mm} mm` : undefined} />
          <SpecRow label="Espessura" value={watch.case_thickness_mm ? `${watch.case_thickness_mm} mm` : undefined} />
          <SpecRow label="Largura de palheta" value={watch.lug_width_mm ? `${watch.lug_width_mm} mm` : undefined} />
          <SpecRow label="Resistência à água" value={watch.water_resistance_m ? `${watch.water_resistance_m} m` : undefined} />
        </SpecCard>

        {/* Dial */}
        <SpecCard title="Mostrador" icon={<Gauge className="w-4 h-4" />}>
          <SpecRow label="Cor" value={watch.dial_color} />
          <SpecRow label="Estilo" value={watch.dial_style} />
          <SpecRow label="Índices" value={watch.dial_indices} />
          {complications.length > 0 && (
            <SpecRow label="Complicações" value={complications.join(", ")} />
          )}
        </SpecCard>

        {/* Bezel */}
        <SpecCard title="Bisel" icon={<Droplets className="w-4 h-4" />}>
          <SpecRow label="Tipo" value={watch.bezel_type} />
          <SpecRow label="Material" value={watch.bezel_material} />
          <SpecRow label="Estilo" value={watch.bezel_style} />
          <SpecRow label="Cor do inserto" value={watch.bezel_insert_color} />
        </SpecCard>

        {/* Movement */}
        <SpecCard title="Movimento" icon={<Zap className="w-4 h-4" />}>
          <SpecRow label="Tipo" value={formatMovement(watch.movement_type)} />
          <SpecRow label="Calibre" value={watch.movement_caliber} />
          <SpecRow label="Rubis" value={watch.movement_jewels} />
          <SpecRow label="Reserva de marcha" value={watch.power_reserve_hours ? `${watch.power_reserve_hours} h` : undefined} />
          <SpecRow label="Frequência" value={watch.frequency_bph ? `${watch.frequency_bph} bph` : undefined} />
        </SpecCard>

        {/* Bracelet */}
        <SpecCard title="Bracelete" icon={<Ruler className="w-4 h-4" />}>
          <SpecRow label="Tipo" value={watch.bracelet_type} />
          <SpecRow label="Material" value={watch.bracelet_material} />
          <SpecRow label="Fecho" value={watch.clasp_type} />
        </SpecCard>

        {/* Hands / Meta */}
        <SpecCard title="Ponteiros &amp; Meta" icon={<Calendar className="w-4 h-4" />}>
          <SpecRow label="Estilo dos ponteiros" value={watch.hand_style} />
          <SpecRow label="Luminescência" value={watch.hand_lume} />
          <SpecRow label="Gênero" value={watch.gender} />
          <SpecRow label="Edição limitada" value={watch.is_limited_edition} />
          {watch.is_limited_edition && (
            <SpecRow label="Quantidade" value={watch.limited_edition_count?.toLocaleString()} />
          )}
        </SpecCard>
      </div>

      {/* ── Similar watches ── */}
      <section>
        <h2 className="text-2xl font-bold text-white mb-6">Relógios Similares</h2>
        <SimilarWatches slug={slug} />
      </section>
    </div>
  );
}
