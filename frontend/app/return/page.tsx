import {SecureReturn} from '@/components/secure-return';
import {Brand} from '@/components/brand';

export default function ReturnPage(){
  return <main className="mx-auto min-h-dvh max-w-2xl space-y-6 px-4 py-8"><Brand/><h1 className="font-display text-3xl">Return to CyberSOS</h1><a href="/incident/start" className="inline-block min-h-11 py-2 underline">Start a conversation</a><SecureReturn/></main>;
}
