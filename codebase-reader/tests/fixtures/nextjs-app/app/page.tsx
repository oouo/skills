import { ClientPanel } from "./client-panel/ClientPanel";

export default async function Page() {
  const initialMessage = "server-rendered";
  return <ClientPanel initialMessage={initialMessage} />;
}
