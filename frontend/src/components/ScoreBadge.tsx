import { cn, scoreColor } from "@/lib/utils";

interface ScoreBadgeProps {
  score: number;
  size?: "sm" | "md";
}

export function ScoreBadge({ score, size = "md" }: ScoreBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center font-bold rounded-full border",
        scoreColor(score),
        size === "sm" ? "text-xs px-2 py-0.5" : "text-sm px-2.5 py-1"
      )}
    >
      {score.toFixed(0)}%
    </span>
  );
}
