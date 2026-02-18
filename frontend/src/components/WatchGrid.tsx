import { WatchCard as WatchCardType } from "@/lib/api";
import { WatchCard } from "./WatchCard";

interface WatchGridProps {
  watches: WatchCardType[];
  showScores?: boolean;
  emptyMessage?: string;
  cols?: 2 | 3 | 4;
  loading?: boolean;
}

export function WatchGrid({ watches, showScores = false, emptyMessage = "Nenhum relógio encontrado.", cols = 4, loading = false }: WatchGridProps) {
  if (loading) {
    const colClass = { 2: "grid-cols-2", 3: "grid-cols-2 sm:grid-cols-3", 4: "grid-cols-2 sm:grid-cols-3 lg:grid-cols-4" }[cols];
    return (
      <div className={`grid ${colClass} gap-4`}>
        {Array.from({ length: cols * 3 }).map((_, i) => (
          <div key={i} className="aspect-[3/4] bg-slate-800 rounded-2xl animate-pulse" />
        ))}
      </div>
    );
  }

  if (!watches.length) {
    return (
      <div className="text-center py-16 text-slate-500">
        <p className="text-4xl mb-3">⌚</p>
        <p>{emptyMessage}</p>
      </div>
    );
  }

  const colClass = {
    2: "grid-cols-2",
    3: "grid-cols-2 sm:grid-cols-3",
    4: "grid-cols-2 sm:grid-cols-3 lg:grid-cols-4",
  }[cols];

  return (
    <div className={`grid ${colClass} gap-4`}>
      {watches.map((w) => (
        <WatchCard key={w.id} watch={w} showScore={showScores} />
      ))}
    </div>
  );
}
