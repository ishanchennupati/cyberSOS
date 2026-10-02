'use client';

import { useEffect } from 'react';
import { reportDiagnostic } from '@/lib/api';

export default function RuntimeDiagnostics() {
  useEffect(() => {
    const onError = (event: ErrorEvent) => {
      // Script names can help locate code; never retain error text or raw stacks.
      let location = 'browser_runtime';
      try {
        const script = new URL(event.filename);
        if (script.origin === window.location.origin && script.pathname.startsWith('/_next/static/')) {
          location = script.pathname;
        }
      } catch { /* No known application script location. */ }
      reportDiagnostic('RUNTIME_ERROR', { location, line: event.lineno, column: event.colno });
    };
    const onRejection = () => reportDiagnostic('UNHANDLED_REJECTION', { location: 'browser_runtime' });
    window.addEventListener('error', onError);
    window.addEventListener('unhandledrejection', onRejection);
    return () => {
      window.removeEventListener('error', onError);
      window.removeEventListener('unhandledrejection', onRejection);
    };
  }, []);
  return null;
}
