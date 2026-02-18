import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatEra(era?: string): string {
  const map: Record<string, string> = {
    vintage: "Vintage",
    transitional: "Transicional",
    modern: "Moderno",
  };
  return era ? (map[era] ?? era) : "—";
}

export function formatStyle(style?: string): string {
  const map: Record<string, string> = {
    diver: "Mergulho",
    dress: "Social",
    sport: "Esportivo",
    pilot: "Piloto",
    field: "Campo",
    racing: "Racing",
    military: "Militar",
    gmt: "GMT",
  };
  return style ? (map[style] ?? style) : "—";
}

export function formatMovement(type?: string): string {
  const map: Record<string, string> = {
    automatic: "Automático",
    manual: "Manual",
    quartz: "Quartzo",
    solar: "Solar",
  };
  return type ? (map[type] ?? type) : "—";
}

export function formatYearRange(start?: number, end?: number): string {
  if (!start) return "—";
  if (!end) return `${start}–presente`;
  return `${start}–${end}`;
}

export function scoreColor(score: number): string {
  if (score >= 85) return "text-emerald-400 bg-emerald-400/10 border-emerald-400/20";
  if (score >= 70) return "text-blue-400 bg-blue-400/10 border-blue-400/20";
  return "text-amber-400 bg-amber-400/10 border-amber-400/20";
}

export function getStyleIcon(style?: string): string {
  const map: Record<string, string> = {
    diver: "🤿",
    dress: "🎩",
    sport: "⚡",
    pilot: "✈️",
    field: "🏕️",
    racing: "🏎️",
    military: "🎖️",
    gmt: "🌍",
  };
  return style ? (map[style] ?? "⌚") : "⌚";
}
