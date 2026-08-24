import EmailItem from "@/components/email-item";

// Same precedence the classifier prompt uses, so the UI mirrors the model's hierarchy.
const CATEGORY_ORDER = [
  "urgent",
  "work",
  "personal",
  "newsletter",
  "promotional",
  "unclassified",
];

export default function EmailList({ emails, onSelect }) {
  if (emails.length === 0) {
    return <p>No emails</p>;
  }

  // Emails only carry a category once /prioritize has run over the inbox.
  const prioritized = emails.some((email) => email.category);

  if (!prioritized) {
    return (
      <ul className="space-y-2">
        {emails.map((email) => (
          <EmailItem key={email.id} email={email} onSelect={onSelect} />
        ))}
      </ul>
    );
  }

  return (
    <div className="space-y-6">
      {CATEGORY_ORDER.map((category) => {
        // The list arrives sorted by score, and filter preserves order,
        // so each section is score-ordered without sorting again.
        const group = emails.filter((email) => email.category === category);
        if (group.length === 0) {
          return null;
        }

        return (
          <section key={category}>
            <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
              {category} ({group.length})
            </h2>
            <ul className="space-y-2">
              {group.map((email) => (
                <EmailItem key={email.id} email={email} onSelect={onSelect} />
              ))}
            </ul>
          </section>
        );
      })}
    </div>
  );
}