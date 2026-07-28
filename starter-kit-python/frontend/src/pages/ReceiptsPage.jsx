import { useEffect, useState } from "react";
import { getReceipts } from "../services/api";

export default function ReceiptsPage() {
  const [receipts, setReceipts] = useState([]);
  const [status, setStatus] = useState("loading"); // loading | ready | error

  useEffect(() => {
    getReceipts()
      .then((res) => {
        setReceipts(res.data);
        setStatus("ready");
      })
      .catch(() => setStatus("error"));
  }, []);

  if (status === "loading") {
    return <p className="text-center text-gray-500 py-16">Loading receipts...</p>;
  }

  if (status === "error") {
    return (
      <p className="text-center text-red-500 py-16">
        Failed to load receipts — is the backend running?
      </p>
    );
  }

  if (receipts.length === 0) {
    return (
      <div className="max-w-lg mx-auto text-center py-16">
        <div className="text-6xl mb-4">🗂️</div>
        <h1 className="text-2xl font-bold text-gray-800 mb-2">Your Receipts</h1>
        <p className="text-gray-500">Upload a receipt to see it here.</p>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-800 mb-6">Your Receipts</h1>
      <div className="space-y-3">
        {receipts.map((r) => (
          <div key={r.filename} className="bg-white border rounded-xl p-4 shadow-sm">
            <div className="flex justify-between items-start">
              <div>
                <p className="font-semibold text-gray-800">
                  {r.store_name || r.filename}
                </p>
                <p className="text-sm text-gray-500">
                  {r.date || new Date(r.uploaded_at * 1000).toLocaleDateString()}
                  {r.category && ` · ${r.category}`}
                </p>
              </div>
              {r.total_amount != null && (
                <p className="font-semibold text-emerald-600">
                  ${Number(r.total_amount).toFixed(2)}
                </p>
              )}
            </div>
            {r.items?.length > 0 && (
              <ul className="mt-3 text-sm text-gray-600 space-y-1 border-t pt-3">
                {r.items.map((item, i) => (
                  <li key={i} className="flex justify-between">
                    <span>{item.name}</span>
                    <span>${Number(item.price).toFixed(2)}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
