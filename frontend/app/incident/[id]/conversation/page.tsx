import { Conversation } from '@/components/conversation';

export default function ConversationPage({ params }: { params: { id: string } }) {
  return <Conversation incidentId={params.id} />;
}
