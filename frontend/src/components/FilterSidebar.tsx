"use client";
import { useState } from "react";
import { FilterOptions } from "@/lib/api";
import { formatStyle, formatMovement } from "@/lib/utils";
import { ChevronDown, ChevronUp, SlidersHorizontal } from "lucide-react";
import { cn } from "@/lib/utils";

interface FilterSidebarProps {
  options: FilterOptions;
  selected: Record<string, string[]>;
  diameterRange: [number, number];
  yearRange: [number, number];
  onChange: (key: string, values: string[]) => void;
  onDiameterChange: (range: [number, number]) => void;
  onYearChange: (range: [number, number]) => void;
  onReset: () => void;
}

function FilterSection({ title, children, defaultOpen = true }: { title: string; children: React.ReactNode; defaultOpen?: boolean }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border-b border-slate-800 pb-4 mb-4">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between text-sm font-semibold text-white mb-3"
      >
        {title}
        {open ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
      </button>
      {open && children}
    </div>
  );
}

function MultiCheckbox({ options, selected, onChange, labelFn }: {
  options: string[];
  selected: string[];
  onChange: (vals: string[]) => void;
  labelFn?: (v: string) => string;
}) {
  const toggle = (v: string) => {
    onChange(selected.includes(v) ? selected.filter((x) => x !== v) : [...selected, v]);
  };
  return (
    <div className="space-y-1.5 max-h-48 overflow-y-auto scrollbar-hide">
      {options.map((opt) => (
        <label key={opt} className="flex items-center gap-2 cursor-pointer group">
          <div className={cn(
            "w-4 h-4 rounded border flex-shrink-0 flex items-center justify-center transition-colors",
            selected.includes(opt) ? "bg-blue-500 border-blue-500" : "border-slate-600 group-hover:border-slate-400"
          )}>
            {selected.includes(opt) && <div className="w-2 h-2 bg-white rounded-sm" />}
          </div>
          <span className="text-sm text-slate-300 group-hover:text-white transition-colors">
            {labelFn ? labelFn(opt) : opt}
          </span>
        </label>
      ))}
    </div>
  );
}

const DIAL_COLORS = [
  { value: "Black", label: "Preto", bg: "bg-black border-slate-600" },
  { value: "White", label: "Branco", bg: "bg-white border-slate-400" },
  { value: "Blue", label: "Azul", bg: "bg-blue-600 border-blue-500" },
  { value: "Silver", label: "Prata", bg: "bg-slate-300 border-slate-400" },
  { value: "Green", label: "Verde", bg: "bg-green-700 border-green-600" },
  { value: "Grey", label: "Cinza", bg: "bg-slate-500 border-slate-400" },
  { value: "Navy Blue", label: "Azul Marinho", bg: "bg-blue-900 border-blue-700" },
];

export function FilterSidebar({
  options, selected, diameterRange, yearRange,
  onChange, onDiameterChange, onYearChange, onReset
}: FilterSidebarProps) {
  const hasAnyFilter = Object.values(selected).some((v) => v.length > 0);

  return (
    <aside className="w-64 shrink-0">
      <div className="sticky top-20">
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-2 text-white font-semibold">
            <SlidersHorizontal className="w-4 h-4" />
            Filtros
          </div>
          {hasAnyFilter && (
            <button onClick={onReset} className="text-xs text-blue-400 hover:text-blue-300">
              Limpar tudo
            </button>
          )}
        </div>

        <FilterSection title="Estilo">
          <MultiCheckbox
            options={options.watch_styles}
            selected={selected.watch_styles || []}
            onChange={(v) => onChange("watch_styles", v)}
            labelFn={formatStyle}
          />
        </FilterSection>

        <FilterSection title="Era">
          <MultiCheckbox
            options={options.eras}
            selected={selected.eras || []}
            onChange={(v) => onChange("eras", v)}
            labelFn={(e) => e === "vintage" ? "Vintage" : e === "transitional" ? "Transicional" : "Moderno"}
          />
        </FilterSection>

        <FilterSection title="Cor do Mostrador">
          <div className="flex flex-wrap gap-2">
            {DIAL_COLORS.filter((dc) => options.dial_colors?.includes(dc.value)).map((dc) => (
              <button
                key={dc.value}
                onClick={() => {
                  const cur = selected.dial_colors || [];
                  onChange("dial_colors", cur.includes(dc.value) ? cur.filter(x => x !== dc.value) : [...cur, dc.value]);
                }}
                title={dc.label}
                className={cn(
                  "w-7 h-7 rounded-full border-2 transition-all",
                  dc.bg,
                  (selected.dial_colors || []).includes(dc.value)
                    ? "ring-2 ring-blue-400 ring-offset-2 ring-offset-slate-950"
                    : "hover:scale-110"
                )}
              />
            ))}
          </div>
        </FilterSection>

        <FilterSection title="Material do Caixa" defaultOpen={false}>
          <MultiCheckbox
            options={options.case_materials}
            selected={selected.case_materials || []}
            onChange={(v) => onChange("case_materials", v)}
          />
        </FilterSection>

        <FilterSection title="Tipo de Bezel" defaultOpen={false}>
          <MultiCheckbox
            options={options.bezel_types}
            selected={selected.bezel_types || []}
            onChange={(v) => onChange("bezel_types", v)}
            labelFn={(b) => ({
              rotating_uni: "Rotativo Unidirecional",
              rotating_bi: "Rotativo Bidirecional",
              fixed: "Fixo",
              none: "Sem bezel"
            }[b] || b)}
          />
        </FilterSection>

        <FilterSection title="Movimento" defaultOpen={false}>
          <MultiCheckbox
            options={options.movement_types}
            selected={selected.movement_types || []}
            onChange={(v) => onChange("movement_types", v)}
            labelFn={formatMovement}
          />
        </FilterSection>

        <FilterSection title="Tamanho do Caixa" defaultOpen={false}>
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm text-slate-400">
              <span>{diameterRange[0]}mm</span>
              <span className="flex-1 text-center">—</span>
              <span>{diameterRange[1]}mm</span>
            </div>
            <div className="flex gap-2">
              <input type="number" min={options.diameter_range.min} max={diameterRange[1]}
                value={diameterRange[0]}
                onChange={(e) => onDiameterChange([Number(e.target.value), diameterRange[1]])}
                className="w-20 bg-slate-800 border border-slate-700 rounded px-2 py-1 text-sm text-white"
              />
              <input type="number" min={diameterRange[0]} max={options.diameter_range.max}
                value={diameterRange[1]}
                onChange={(e) => onDiameterChange([diameterRange[0], Number(e.target.value)])}
                className="w-20 bg-slate-800 border border-slate-700 rounded px-2 py-1 text-sm text-white"
              />
            </div>
          </div>
        </FilterSection>

        <FilterSection title="Período" defaultOpen={false}>
          <div className="flex gap-2">
            <input type="number" min={options.year_range.min} max={yearRange[1]}
              value={yearRange[0]}
              onChange={(e) => onYearChange([Number(e.target.value), yearRange[1]])}
              className="w-20 bg-slate-800 border border-slate-700 rounded px-2 py-1 text-sm text-white"
            />
            <input type="number" min={yearRange[0]} max={options.year_range.max}
              value={yearRange[1]}
              onChange={(e) => onYearChange([yearRange[0], Number(e.target.value)])}
              className="w-20 bg-slate-800 border border-slate-700 rounded px-2 py-1 text-sm text-white"
            />
          </div>
        </FilterSection>

        <FilterSection title="Marca" defaultOpen={false}>
          <div className="space-y-1.5 max-h-48 overflow-y-auto scrollbar-hide">
            {options.brands.map((b) => {
              const cur = selected.brand_ids || [];
              const val = String(b.id);
              return (
                <label key={b.id} className="flex items-center gap-2 cursor-pointer group">
                  <div className={cn(
                    "w-4 h-4 rounded border flex-shrink-0 flex items-center justify-center transition-colors",
                    cur.includes(val) ? "bg-blue-500 border-blue-500" : "border-slate-600 group-hover:border-slate-400"
                  )}>
                    {cur.includes(val) && <div className="w-2 h-2 bg-white rounded-sm" />}
                  </div>
                  <span className="text-sm text-slate-300 group-hover:text-white">{b.name}</span>
                </label>
              );
            })}
          </div>
        </FilterSection>
      </div>
    </aside>
  );
}
