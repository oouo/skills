"use client";

import { useState } from "react";

export function ClientPanel({ initialMessage }: { initialMessage: string }) {
  const [message, setMessage] = useState(initialMessage);

  async function submit() {
    const response = await fetch("/api/chat", {
      method: "POST",
      body: JSON.stringify({ message }),
    });
    const data = (await response.json()) as { reply: string };
    setMessage(data.reply);
  }

  return <button onClick={submit}>{message}</button>;
}
