"use client";
import { useState, useEffect, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Search, Camera, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { searchApi, AutocompleteResult } from "@/lib/api";

interface SearchBarProps {
  compact?: boolean;
  onImageFile?: (file: File) => void;
  defaultValue?: string;
}

export function SearchBar({ compact = false, onImageFile, defaultValue = "" }: SearchBarProps) {
  const router = useRouter();
  const [query, setQuery] = useState(defaultValue);
  const [suggestions, setSuggestions] = useState<AutocompleteResult["suggestions"]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  const fetchSuggestions = useCallback(async (q: string) => {
    if (q.length < 2) { setSuggestions([]); return; }
    setLoadingSuggestions(true);
    try {
      const data = await searchApi.autocomplete(q);
      setSuggestions(data.suggestions);
    } catch {
      setSuggestions([]);
    } finally {
      setLoadingSuggestions(false);
    }
  }, []);

  useEffect(() => {
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => fetchSuggestions(query), 300);
    return () => clearTimeout(debounceRef.current);
  }, [query, fetchSuggestions]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    setShowSuggestions(false);
    router.push(`/search?q=${encodeURIComponent(query.trim())}`);
  };

  const handleSuggestionClick = (s: AutocompleteResult["suggestions"][0]) => {
    setShowSuggestions(false);
    if (s.type === "watch") {
      router.push(`/watch/${s.slug}`);
    } else {
      router.push(`/search?q=${encodeURIComponent(s.label)}`);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (onImageFile) {
      onImageFile(file);
    } else {
      router.push("/search?mode=image");
    }
  };

  return (
    <form onSubmit={handleSubmit} className="relative w-full">
      <div
        className={cn(
          "flex items-center gap-2 rounded-xl border border-slate-700 bg-slate-900 transition-all",
          "focus-within:border-blue-500 focus-within:ring-1 focus-within:ring-blue-500/30",
          compact ? "px-3 py-2" : "px-4 py-3"
        )}
      >
        <Search className={cn("text-slate-400 shrink-0", compact ? "w-4 h-4" : "w-5 h-5")} />
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => { setQuery(e.target.value); setShowSuggestions(true); }}
          onFocus={() => setShowSuggestions(true)}
          onBlur={() => setTimeout(() => setShowSuggestions(false), 150)}
          placeholder={compact ? "Buscar relógios..." : "Buscar por marca, modelo ou referência..."}
          className={cn(
            "flex-1 bg-transparent outline-none placeholder-slate-500 text-white",
            compact ? "text-sm" : "text-base"
          )}
        />
        {query && (
          <button type="button" onClick={() => { setQuery(""); setSuggestions([]); }}
            className="text-slate-500 hover:text-white transition-colors">
            <X className="w-4 h-4" />
          </button>
        )}
        <button
          type="button"
          onClick={() => fileRef.current?.click()}
          className="text-slate-400 hover:text-blue-400 transition-colors"
          title="Buscar por imagem"
        >
          <Camera className={cn(compact ? "w-4 h-4" : "w-5 h-5")} />
        </button>
        <input ref={fileRef} type="file" accept="image/*" className="hidden" onChange={handleFileChange} />
      </div>

      {/* Suggestions dropdown */}
      {showSuggestions && suggestions.length > 0 && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-slate-900 border border-slate-700 rounded-xl shadow-2xl overflow-hidden z-50">
          {suggestions.map((s) => (
            <button
              key={`${s.type}-${s.id}`}
              type="button"
              onMouseDown={() => handleSuggestionClick(s)}
              className="w-full px-4 py-2.5 text-left flex items-center gap-3 hover:bg-slate-800 transition-colors"
            >
              <span className="text-xs px-1.5 py-0.5 rounded bg-slate-700 text-slate-300 capitalize shrink-0">
                {s.type === "watch" ? "relógio" : s.type === "brand" ? "marca" : "coleção"}
              </span>
              <span className="text-sm text-white truncate">{s.label}</span>
            </button>
          ))}
        </div>
      )}
    </form>
  );
}
