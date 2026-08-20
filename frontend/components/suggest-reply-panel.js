export default function SuggestReplyPanel({ response, loading }) {
  if (loading) {
    return <p className="mt-4 text-sm text-gray-400">Generating possible response</p>;
  }

  if (!response) {
    return null;
  }

  return (
    <div className="mt-4 rounded border border-gray-700 p-3">
      <p className="mb-2 text-xs font-semibold uppercase text-gray-400">
        Suggestion:
      </p>
      <pre className="whitespace-pre-wrap font-sans text-sm">{response}</pre>
    </div>
  );
}
