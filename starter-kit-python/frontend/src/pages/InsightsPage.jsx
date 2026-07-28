import { useEffect, useState } from "react";
import { getInsights } from "../services/api";

export default function InsightsPage() {
  const [insights, setInsights] = useState(null);
  const [message, setMessage] = useState(null);
  const [status, setStatus] = useState("loading"); // loading | ready | error

  useEffect(() => {
    getInsights()
      .then((res) => {
        setInsights(res.data.insights);
        setMessage(res.data.message);
        setStatus("ready");
      })
      .catch(() => setStatus("error"));
  }, []);

  if (status === "loading") {
    return <p className="text-center text-gray-500 py-16">Analysing your spending...</p>;
  }

  if (status === "error") {
    return (
      <p className="text-center text-red-500 py-16">
        Failed to load insights — is the backend running?
      </p>
    );
  }

  if (!insights) {
    return (
      <div className="max-w-lg mx-auto text-center py-16">
        <div className="text-6xl mb-4">📊</div>
        <h1 className="text-2xl font-bold text-gray-800 mb-2">Spending Insights</h1>
        <p className="text-gray-500">
          {message || "Upload some receipts to get insights!"}
        </p>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-800 mb-6">Spending Insights</h1>
      <div className="bg-white border rounded-xl p-6 shadow-sm whitespace-pre-wrap text-gray-700">
        {insights}
      </div>
    </div>
  );
}
