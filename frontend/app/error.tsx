'use client';

import { useEffect } from 'react';
import { reportDiagnostic } from '@/lib/api';

export default function ErrorPage({ error, reset }: { error: Error; reset: () => void }) {
  useEffect(() => { reportDiagnostic('RENDER_ERROR', { location: 'route_error_boundary' }); }, [error]);
  return <main className="mx-auto max-w-2xl p-6" role="alert">
    <h1 className="text-2xl font-medium">CyberSOS could not display this page.</h1>
    <p className="mt-3">Try loading it again. You can review your saved conversation once the page opens.</p>
    <button className="mt-4 min-h-12 rounded border border-line px-4" onClick={reset}>Try again</button>
  </main>;
}
