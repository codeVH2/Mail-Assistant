export default function EmailItem({ email, onSelect }) {
  return (
    <li
      onClick={() => onSelect(email.id)}
      className="cursor-pointer rounded border p-3 hover:bg-gray-800"
    >
      <div className="flex items-start justify-between gap-2">
        <p className="font-semibold">{email.sender}</p>
        {email.score !== undefined && (
          <span className="shrink-0 text-sm text-gray-400">
            {email.score.toFixed(2)}
          </span>
        )}
      </div>
      <p className="text-sm">{email.subject}</p>
      <p className="text-sm text-gray-500">{email.snippet}</p>
    </li>
  );
}
