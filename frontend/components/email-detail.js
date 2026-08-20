"use client";
import { useState } from "react";
import { suggestReply } from "@/lib/api";
import SuggestReplyPanel from "@/components/suggest-reply-panel";

export default function EmailDetail({ email }) {
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);

  async function handleSuggestReply() {
    setLoading(true);
    try {
      const aiResponse = await suggestReply(email.id);
      setResponse(aiResponse.response);
    } catch (error) {
      console.error("Error on AI response suggestion:", error);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="rounded border border-gray-700 p-4">
      <h2 className="text-xl font-bold">{email.subject}</h2>
      <p className="text-sm text-gray-400 mb-4">{email.sender}</p>
      <pre className="whitespace-pre-wrap font-sans text-sm">{email.body}</pre>
      <button
        className="rounded border border-amber-600 cursor-pointer"
        onClick={handleSuggestReply}
        disabled={loading}
      >
        Reply suggestion
      </button>
      <SuggestReplyPanel response={response} loading={loading} />
    </div>
  );
}
