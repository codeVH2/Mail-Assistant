const BACKEND_API = process.env.NEXT_PUBLIC_BACKEND_API;

async function request(path, options) {
  const res = await fetch(`${BACKEND_API}${path}`, options);
  if (!res.ok) {
    throw new Error(`API request failed with status ${res.status} : ${res.statusText}`);
  }

  return res.json();
}

// GET /emails → list of {id, threadId, subject, sender, snippet}
export const listEmails = () => request("/emails", { method: "GET" });

// GET /emails/{id} → {subject, sender, body}
export const getEmail = (id) => request(`/emails/${id}`, { method: "GET" });

// POST /emails/{id}/reply-suggest → {response}
export const suggestReply = (id, providerName) =>
  request(`/emails/${id}/reply-suggest?provider_name=${providerName}`, {method: "POST" });

// POST /emails/{id}/prioritize → {category, score}
export const prioritize = (id, providerName) =>
  request(`/emails/${id}/prioritize?provider_name=${providerName}`, { method: "POST" });

// GET /auth/status → {authenticated}
export const authStatus = () => request("/auth/status", { method: "GET" });
