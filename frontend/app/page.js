"use client";
import { useState, useEffect } from "react";
import { authStatus } from "@/lib/api";
import LoginButton from "@/components/login-button";

export default function Home() {
  const [authenticated, setAuthenticated] = useState(null);

  useEffect(() => {
    authStatus()
      .then((data) => {
        setAuthenticated(data.authenticated);
      })
      .catch((error) => {
        console.error("Error fetching authentication status:", error);
      });
  }, []);

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
  return (
    <main className="p-8">
      <h1 className="text-2xl font-bold mb-4">Inbox</h1>
      <p>Authenticated!!!dwdasd</p>
    </main>
  );
}
