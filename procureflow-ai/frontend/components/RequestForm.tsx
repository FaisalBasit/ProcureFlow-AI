"use client";

import { useState, FormEvent } from "react";

interface RequestFormProps {
  onSubmit: (data: {
    vendor_name: string;
    amount: number;
    category: string;
    justification: string;
  }) => Promise<void>;
  loading: boolean;
}

const CATEGORIES = [
  "software",
  "hardware",
  "consulting",
  "services",
  "supplies",
  "capital",
  "other",
];

export default function RequestForm({ onSubmit, loading }: RequestFormProps) {
  const [vendorName, setVendorName] = useState("");
  const [amount, setAmount] = useState("");
  const [category, setCategory] = useState("software");
  const [justification, setJustification] = useState("");

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    await onSubmit({
      vendor_name: vendorName,
      amount: parseFloat(amount),
      category,
      justification,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="card">
      <h2 className="card-title">📋 New Purchase Request</h2>

      <div className="form-group">
        <label className="form-label" htmlFor="vendorName">
          Vendor Name
        </label>
        <input
          id="vendorName"
          className="form-input"
          type="text"
          placeholder="e.g., Acme Cloud Services"
          value={vendorName}
          onChange={(e) => setVendorName(e.target.value)}
          required
          minLength={2}
          disabled={loading}
        />
      </div>

      <div className="form-group">
        <label className="form-label" htmlFor="amount">
          Amount (USD)
        </label>
        <input
          id="amount"
          className="form-input"
          type="number"
          placeholder="e.g., 15000"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          required
          min="0.01"
          step="0.01"
          disabled={loading}
        />
      </div>

      <div className="form-group">
        <label className="form-label" htmlFor="category">
          Category
        </label>
        <select
          id="category"
          className="form-select"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          disabled={loading}
        >
          {CATEGORIES.map((cat) => (
            <option key={cat} value={cat}>
              {cat.charAt(0).toUpperCase() + cat.slice(1)}
            </option>
          ))}
        </select>
      </div>

      <div className="form-group">
        <label className="form-label" htmlFor="justification">
          Business Justification
        </label>
        <textarea
          id="justification"
          className="form-textarea"
          placeholder="Describe why this purchase is needed..."
          value={justification}
          onChange={(e) => setJustification(e.target.value)}
          required
          minLength={10}
          disabled={loading}
        />
      </div>

      <button type="submit" className="btn btn-primary" disabled={loading}>
        {loading ? (
          <>
            <span className="spinner" style={{ width: 16, height: 16 }} />
            Processing...
          </>
        ) : (
          "🚀 Submit Request"
        )}
      </button>
    </form>
  );
}