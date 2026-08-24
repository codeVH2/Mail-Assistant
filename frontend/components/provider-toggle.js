export default function ProviderToggle({ value, onChange }) {
  return (
    <div>
      <label className="flex items-center gap-2 text-sm">
        <span className="text-gray-400">AI provider</span>
        <select
          value={value}
          onChange={(event) => onChange(event.target.value)}
          className="rounded border border-gray-600 bg-transparent px-2 py-1"
        >
          <option value="local">Local (llama3.1:8b)</option>
          <option value="cloud">Cloud (Claude)</option>
        </select>
      </label>

      {/* Cloud processing sends content off the machine, so the trade-off is
          stated up front rather than buried in settings. */}
      {value === "cloud" && (
        <p className="mt-2 rounded border border-amber-600 bg-amber-950/40 px-3 py-2 text-sm text-amber-400">
          Email content will be sent to Anthropic (US) for processing. Switch
          back to Local to keep it on this machine.
        </p>
      )}
    </div>
  );
}