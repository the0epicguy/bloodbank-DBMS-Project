import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  fetchAllBanks,
  createBank,
  updateBank,
  deleteBank,
} from "../../api/inventory";
import type { BloodBank, BloodBankCreate } from "../../types";

// -----------------------------------------------------------------------
// Bank Form Modal
// -----------------------------------------------------------------------
interface BankFormProps {
  initial?: Partial<BloodBank>;
  onSubmit: (data: BloodBankCreate) => void;
  onCancel: () => void;
  isLoading: boolean;
}

function BankFormModal({ initial, onSubmit, onCancel, isLoading }: BankFormProps) {
  const [form, setForm] = useState<BloodBankCreate>({
    name:    initial?.name    ?? "",
    address: initial?.address ?? "",
    city:    initial?.city    ?? "",
    contact: initial?.contact ?? "",
    email:   initial?.email   ?? "",
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-lg shadow-2xl">
        <div className="px-6 py-5 border-b border-slate-700">
          <h2 className="text-lg font-bold text-white">
            {initial?.bank_id ? "Edit Blood Bank" : "Register New Blood Bank"}
          </h2>
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            onSubmit(form);
          }}
          className="px-6 py-5 space-y-4"
        >
          {(
            [
              { name: "name",    label: "Bank Name",      type: "text",  required: true  },
              { name: "address", label: "Address",        type: "text",  required: true  },
              { name: "city",    label: "City",           type: "text",  required: true  },
              { name: "contact", label: "Contact Phone",  type: "text",  required: true  },
              { name: "email",   label: "Email (optional)", type: "email", required: false },
            ] as const
          ).map(({ name, label, type, required }) => (
            <div key={name}>
              <label className="block text-xs font-medium text-slate-400 mb-1.5 uppercase tracking-wider">
                {label} {required && <span className="text-rose-500">*</span>}
              </label>
              <input
                id={`bank-form-${name}`}
                name={name}
                type={type}
                required={required}
                value={form[name as keyof BloodBankCreate] ?? ""}
                onChange={handleChange}
                className="w-full bg-slate-800 border border-slate-600 text-white placeholder-slate-500 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-rose-500/50 focus:border-rose-500 transition-colors"
                placeholder={`Enter ${label.toLowerCase()}`}
              />
            </div>
          ))}

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onCancel}
              className="flex-1 bg-slate-700 hover:bg-slate-600 text-white rounded-lg py-2.5 text-sm font-medium transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="flex-1 bg-rose-600 hover:bg-rose-700 disabled:opacity-50 text-white rounded-lg py-2.5 text-sm font-semibold transition-colors"
            >
              {isLoading ? "Saving..." : initial?.bank_id ? "Save Changes" : "Register Bank"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// -----------------------------------------------------------------------
// Main BankList page
// -----------------------------------------------------------------------
export default function BankList() {
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [editingBank, setEditingBank] = useState<BloodBank | null>(null);
  const [deleteConfirmId, setDeleteConfirmId] = useState<number | null>(null);

  const { data: banks = [], isLoading } = useQuery({
    queryKey: ["banks"],
    queryFn: fetchAllBanks,
  });

  const createMutation = useMutation({
    mutationFn: createBank,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["banks"] });
      setShowForm(false);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: BloodBankCreate }) =>
      updateBank(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["banks"] });
      setEditingBank(null);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteBank,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["banks"] });
      setDeleteConfirmId(null);
    },
  });

  const filtered = banks.filter(
    (b) =>
      b.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      b.city.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-slate-950 text-white p-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">🏥 Blood Bank Management</h1>
          <p className="text-slate-400 text-sm mt-1">
            Register and manage blood bank centers
          </p>
        </div>
        <button
          id="btn-register-bank"
          onClick={() => setShowForm(true)}
          className="flex items-center gap-2 bg-rose-600 hover:bg-rose-700 text-white text-sm font-semibold px-4 py-2 rounded-lg transition-colors shadow-lg shadow-rose-900/30"
        >
          + Register Blood Bank
        </button>
      </div>

      {/* Search bar */}
      <div className="relative mb-5 max-w-sm">
        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-sm">🔍</span>
        <input
          id="bank-search"
          type="text"
          placeholder="Search by name or city..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full bg-slate-800 border border-slate-700 text-white pl-9 pr-4 py-2.5 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-rose-500/40 focus:border-rose-500 transition-colors"
        />
      </div>

      {/* Banks Table */}
      {isLoading ? (
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-16 rounded-xl bg-slate-800 animate-pulse" />
          ))}
        </div>
      ) : (
        <div className="bg-slate-900 rounded-2xl border border-slate-700 overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="bg-slate-800/80 text-xs text-slate-400 uppercase tracking-wider">
                <th className="text-left px-5 py-3.5">Name</th>
                <th className="text-left px-5 py-3.5 hidden md:table-cell">City</th>
                <th className="text-left px-5 py-3.5 hidden lg:table-cell">Contact</th>
                <th className="text-center px-5 py-3.5">Available</th>
                <th className="text-center px-5 py-3.5">Expiring</th>
                <th className="text-center px-5 py-3.5">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-500 text-sm">
                    No blood banks found.
                  </td>
                </tr>
              ) : (
                filtered.map((bank) => (
                  <tr
                    key={bank.bank_id}
                    className="hover:bg-slate-800/40 transition-colors group"
                  >
                    <td className="px-5 py-4">
                      <p className="font-medium text-white text-sm">{bank.name}</p>
                      <p className="text-xs text-slate-500 mt-0.5 truncate max-w-[200px]">
                        {bank.address}
                      </p>
                    </td>
                    <td className="px-5 py-4 hidden md:table-cell text-sm text-slate-300">
                      {bank.city}
                    </td>
                    <td className="px-5 py-4 hidden lg:table-cell text-sm text-slate-400">
                      {bank.contact}
                    </td>
                    <td className="px-5 py-4 text-center">
                      <span className="text-emerald-400 font-bold text-sm">
                        {bank.available_units}
                      </span>
                    </td>
                    <td className="px-5 py-4 text-center">
                      {bank.expiring_soon > 0 ? (
                        <span className="text-amber-400 font-semibold text-sm flex items-center justify-center gap-1">
                          <span className="animate-pulse">⚠</span> {bank.expiring_soon}
                        </span>
                      ) : (
                        <span className="text-slate-600 text-sm">—</span>
                      )}
                    </td>
                    <td className="px-5 py-4 text-center">
                      <div className="flex items-center justify-center gap-2">
                        <button
                          id={`btn-edit-bank-${bank.bank_id}`}
                          onClick={() => setEditingBank(bank)}
                          className="text-xs text-slate-400 hover:text-white bg-slate-700 hover:bg-slate-600 px-2.5 py-1 rounded-md transition-colors"
                        >
                          Edit
                        </button>
                        <button
                          id={`btn-delete-bank-${bank.bank_id}`}
                          onClick={() => setDeleteConfirmId(bank.bank_id)}
                          className="text-xs text-rose-400 hover:text-white bg-rose-900/30 hover:bg-rose-700 px-2.5 py-1 rounded-md transition-colors"
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Create / Edit modal */}
      {(showForm || editingBank) && (
        <BankFormModal
          initial={editingBank ?? undefined}
          isLoading={createMutation.isPending || updateMutation.isPending}
          onSubmit={(data) => {
            if (editingBank) {
              updateMutation.mutate({ id: editingBank.bank_id, data });
            } else {
              createMutation.mutate(data);
            }
          }}
          onCancel={() => {
            setShowForm(false);
            setEditingBank(null);
          }}
        />
      )}

      {/* Delete confirmation */}
      {deleteConfirmId !== null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-rose-800 rounded-2xl p-6 max-w-sm w-full text-center shadow-2xl">
            <div className="text-4xl mb-3">⚠️</div>
            <h3 className="text-lg font-bold text-white mb-2">Delete Blood Bank?</h3>
            <p className="text-slate-400 text-sm mb-5">
              This will permanently delete the blood bank and all its blood unit records. This action cannot be undone.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setDeleteConfirmId(null)}
                className="flex-1 bg-slate-700 hover:bg-slate-600 text-white rounded-lg py-2.5 text-sm font-medium transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => deleteConfirmId !== null && deleteMutation.mutate(deleteConfirmId)}
                disabled={deleteMutation.isPending}
                className="flex-1 bg-rose-600 hover:bg-rose-700 disabled:opacity-50 text-white rounded-lg py-2.5 text-sm font-semibold transition-colors"
              >
                {deleteMutation.isPending ? "Deleting..." : "Yes, Delete"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
