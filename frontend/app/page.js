"use client";
import { useState, useEffect } from "react";
import { authStatus, getEmail, listEmails, prioritize } from "@/lib/api";
import LoginButton from "@/components/login-button";
import EmailList from "@/components/email-list";
import EmailDetail from "@/components/email-detail";
import ProviderToggle from "@/components/provider-toggle";

export default function Home() {
  const [authenticated, setAuthenticated] = useState(null);
  const [emails, setEmails] = useState([]);
  const [selectedEmail, setSelectedEmail] = useState(null);
  const [prioritizing, setPrioritizing] = useState(false);
  const [aiProvider, setAiProvider] = useState("local");

  useEffect(() => {
    authStatus()
      .then((data) => {
        setAuthenticated(data.authenticated);
      })
      .catch((error) => {
        console.error("Error fetching authentication status:", error);
        setAuthenticated(false);
      });
  }, []);

  useEffect(() => {
    if (authenticated) {
      listEmails()
        .then((data) => {
          setEmails(data);
        })
        .catch((error) => {
          console.error("Error fetching emails status:", error);
          setEmails([]);
        });
    }
  }, [authenticated]);

  if (authenticated === null) {
    return <p>Loading...</p>;
  }

  if (!authenticated) {
    return (
      <main className="p-8">
        <h1 className="text-2xl font-bold mb-4">Mail Assistant</h1>
        <LoginButton />
      </main>
    );
  }

  function selectEmail(id) {
    getEmail(id)
      .then((data) => setSelectedEmail({ ...data, id }))
      .catch((error) =>
        console.error("Error selecting a specifi email status:", error),
      );
  }

  async function handlePrioritizeAll() {
    setPrioritizing(true);
    try {
      const result = await Promise.all(
        emails.map((email) =>
          prioritize(email.id, aiProvider)
            .then((data) => {
              return { ...email, ...data };
            })
            .catch(() => {
              return { ...email, category: "unclassified", score: 0 }; //if classification fails, default values
            }),
        ),
      );
      const sorted = [...result].sort((a, b) => b.score - a.score);
      setEmails(sorted);
    } catch (error) {
      console.error("Error os prioritizing:", error);
    } finally {
      setPrioritizing(false);
    }
  }

  return (
    <main className="p-8">
      <h1 className="text-4xl font-bold mb-4">Inbox</h1>

      <div className="mb-4">
        <ProviderToggle value={aiProvider} onChange={setAiProvider} />
      </div>

      <button
        onClick={handlePrioritizeAll}
        disabled={prioritizing}
        className="mb-4 rounded bg-blue-600 px-4 py-2 text-white disabled:opacity-50"
      >
        {prioritizing ? "Classifying..." : "Prioritize & categorize"}
      </button>

      <div className="flex gap-6">
        <div className="w-1/2">
          <EmailList emails={emails} onSelect={selectEmail} />
        </div>
        <div className="w-1/2">
          {selectedEmail && (
            <EmailDetail
              key={selectedEmail.id}
              email={selectedEmail}
              aiProvider={aiProvider}
            />
          )}
        </div>
      </div>
    </main>
  );
}
