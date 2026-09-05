export default function ProviderToggle({ value, handleProviderChange }) {
  return (
    <div>
      <label className="flex items-center gap-2 text-sm">
        <span className="text-gray-400">AI provider</span>
        <select
          value={value}
          onChange={(event) => handleProviderChange(event.target.value)}
          className="rounded border border-gray-600 bg-transparent px-2 py-1"
        >
          <option value="local">Local (llama3.1:8b)</option>
          <option value="cloud">Cloud (Claude)</option>
        </select>
      </label>

      {/* Cloud processing sends content off the machine, so the trade-off is
          stated up front rather than buried in settings. */}
      {value === "cloud" && (
        <p className="mt-2 rounded border border-red-900 bg-red-100 px-3 py-2 text-sm font-semibold text-gray-900 te">
          Email content will be sent to Anthropic (US) for processing. Switch
          back to Local to keep it on this machine.
        </p>
      )}
    </div>
  );
}