"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft } from "lucide-react";

import { ErrorState } from "@/components/error-state";
import { LoadingState } from "@/components/loading-state";
import { ResultScreen } from "@/components/result-screen";
import { ApiError, getActionPlan } from "@/lib/api";
import type { ActionPlan } from "@/types/incident";

export default function IncidentResultPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  const [plan, setPlan] = useState<ActionPlan | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const data = await getActionPlan(id);
      setPlan(data);
    } catch (err) {
      setPlan(null);
      setError(
        err instanceof ApiError ? err.message : "We couldn't load your action plan. Please try again."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  return (
    <main className="min-h-screen bg-paper">
      <header className="border-b border-line bg-surface">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-6 py-4">
          <div className="flex gap-4">
            <Link href="/" className="flex items-center gap-2 text-sm text-ink-muted hover:text-ink">
              <ArrowLeft size={16} aria-hidden="true" />
              Home
            </Link>
            <Link href={`/incident/${id}/conversation`} className="flex items-center gap-2 text-sm text-ink-muted hover:text-ink border-l border-line pl-4">
              Edit answers
            </Link>
          </div>
          <span className="font-display text-lg italic text-ink">CyberSOS</span>
        </div>
      </header>

      <div className="mx-auto max-w-3xl px-6 py-10">
        <div className="mt-10">
          {loading && <LoadingState message="Loading your action plan…" />}
          {error && !loading && <ErrorState message={error} onRetry={load} />}
          {plan && !loading && <ResultScreen plan={plan} incidentId={id} />}
        </div>
      </div>
    </main>
  );
}
