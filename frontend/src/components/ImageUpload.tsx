"use client";
import { useState, useCallback, useRef } from "react";
import Image from "next/image";
import { Camera, Upload, X, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { searchApi, ImageSearchResponse } from "@/lib/api";

interface ImageUploadProps {
  onResult: (result: ImageSearchResponse) => void;
}

export function ImageUpload({ onResult }: ImageUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const processFile = useCallback(async (file: File) => {
    if (!file.type.startsWith("image/")) {
      setError("Por favor, envie uma imagem (JPEG, PNG ou WebP).");
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setError("Imagem muito grande. Máximo 10MB.");
      return;
    }
    setError(null);
    setPreview(URL.createObjectURL(file));
    setLoading(true);
    try {
      const result = await searchApi.byImage(file);
      onResult(result);
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? "Erro ao processar imagem. Tente novamente.");
    } finally {
      setLoading(false);
    }
  }, [onResult]);

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) processFile(file);
  }, [processFile]);

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) processFile(file);
  };

  const clear = () => {
    setPreview(null);
    setError(null);
    if (fileRef.current) fileRef.current.value = "";
  };

  return (
    <div className="w-full">
      {preview ? (
        <div className="relative rounded-2xl overflow-hidden border border-slate-700 bg-slate-900">
          <div className="relative aspect-square max-w-xs mx-auto">
            <Image src={preview} alt="Imagem enviada" fill className="object-contain p-4" />
          </div>
          {loading && (
            <div className="absolute inset-0 bg-black/60 flex flex-col items-center justify-center gap-3">
              <Loader2 className="w-8 h-8 text-blue-400 animate-spin" />
              <p className="text-white text-sm font-medium">Buscando correspondências...</p>
            </div>
          )}
          {!loading && (
            <button
              onClick={clear}
              className="absolute top-3 right-3 bg-slate-800 hover:bg-slate-700 text-white rounded-full p-1.5 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      ) : (
        <div
          onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={onDrop}
          onClick={() => fileRef.current?.click()}
          className={cn(
            "rounded-2xl border-2 border-dashed p-10 text-center cursor-pointer transition-all",
            isDragging
              ? "border-blue-400 bg-blue-400/5"
              : "border-slate-700 hover:border-slate-500 hover:bg-slate-800/50"
          )}
        >
          <Camera className="w-12 h-12 text-slate-500 mx-auto mb-3" />
          <p className="text-white font-medium mb-1">Arraste uma foto de relógio aqui</p>
          <p className="text-slate-500 text-sm mb-4">ou clique para selecionar</p>
          <span className="inline-flex items-center gap-2 text-sm text-blue-400 border border-blue-400/30 rounded-lg px-4 py-2">
            <Upload className="w-4 h-4" />
            Selecionar imagem
          </span>
        </div>
      )}
      {error && (
        <p className="mt-2 text-sm text-red-400 text-center">{error}</p>
      )}
      <input ref={fileRef} type="file" accept="image/*,image/heic" className="hidden" onChange={onFileChange} />
    </div>
  );
}
