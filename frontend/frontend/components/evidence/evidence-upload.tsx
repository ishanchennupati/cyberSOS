"use client";

import { useRef, useState } from "react";
import { Upload } from "lucide-react";

import { cn } from "@/lib/utils";

const ACCEPTED_EXTENSIONS = [".png", ".jpg", ".jpeg", ".pdf"];
const ACCEPTED_MIME = ["image/png", "image/jpeg", "application/pdf"];
const MAX_SIZE_MB = 10;

interface EvidenceUploadProps {
  onFileSelected: (file: File) => void;
  disabled?: boolean;
  error?: string | null;
}

export function EvidenceUpload({ onFileSelected, disabled, error }: EvidenceUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  function validateAndSelect(file: File) {
    setLocalError(null);
    const ext = "." + (file.name.split(".").pop() ?? "").toLowerCase();
    if (!ACCEPTED_EXTENSIONS.includes(ext) || !ACCEPTED_MIME.includes(file.type)) {
      setLocalError(
        `"${file.name}" isn't a supported file type. Please upload a PNG, JPG, or PDF.`
      );
      return;
    }
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      setLocalError(`This file is too large. Evidence files must be under ${MAX_SIZE_MB} MB.`);
      return;
    }
    onFileSelected(file);
  }

  function handleDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setDragActive(false);
    if (disabled) return;
    const file = e.dataTransfer.files?.[0];
    if (file) validateAndSelect(file);
  }

  return (
    <div>
      <div
        role="button"
        tabIndex={disabled ? -1 : 0}
        aria-disabled={disabled}
        aria-label="Upload evidence — click to choose a file or drag and drop"
        onClick={() => !disabled && inputRef.current?.click()}
        onKeyDown={(e) => {
          if ((e.key === "Enter" || e.key === " ") && !disabled) {
            e.preventDefault();
            inputRef.current?.click();
          }
        }}
        onDragOver={(e) => {
          e.preventDefault();
          if (!disabled) setDragActive(true);
        }}
        onDragLeave={() => setDragActive(false)}
        onDrop={handleDrop}
        className={cn(
          "flex min-h-[160px] cursor-pointer flex-col items-center justify-center gap-3 rounded-lg border-2 border-dashed px-6 py-10 text-center transition-colors",
          dragActive ? "border-calm bg-calm-soft" : "border-line2 bg-surface hover:border-ink",
          disabled && "cursor-not-allowed opacity-60"
        )}
      >
        <span className="flex h-12 w-12 items-center justify-center rounded-full bg-calm-soft text-calm">
          <Upload size={22} aria-hidden="true" />
        </span>
        <div>
          <p className="font-medium text-ink">+ Upload evidence</p>
          <p className="mt-1 text-sm text-ink-muted">
            Drag and drop, or click to choose a file. PNG, JPG, or PDF, up to {MAX_SIZE_MB} MB.
          </p>
        </div>
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED_EXTENSIONS.join(",")}
          className="sr-only"
          disabled={disabled}
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) validateAndSelect(file);
            e.target.value = "";
          }}
        />
      </div>
      {(localError || error) && (
        <p role="alert" className="mt-2 text-sm text-urgent">
          {localError || error}
        </p>
      )}
    </div>
  );
}
