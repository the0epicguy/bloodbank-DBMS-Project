import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  fetchAllBanks,
  fetchGlobalSummary,
  runExpirySweep,
} from "../../api/inventory";
import type { BloodBank, BloodGroup, ComponentType } from "../../types";

// -----------------------------------------------------------------------
// Constants
// -----------------------------------------------------------------------
const BLOOD_GROUPS: BloodGroup[] = [
  "O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+",
];
const COMPONENTS: ComponentType[] = [
  "WHOLE_BLOOD", "RBC", "PLATELETS", "PLASMA",
];
const COMPONENT_LABELS: Record<ComponentType, string> = {
  WHOLE_BLOOD: "Whole Blood",
  RBC:         "RBC",
  PLATELETS:   "Platelets",
  PLASMA:      "Plasma",
};

// -----------------------------------------------------------------------
// Utilities
// -----------------------------------------------------------------------
function expiryColor(daysToExpiry: number | undefined): string {
  if (daysToExpiry === undefined || daysToExpiry === null) return "bg-slate-700";
  if (daysToExpiry <= 3)  return "bg-red-600";
  if (daysToExpiry <= 7)  return "bg-amber-500";
  if (daysToExpiry <= 14) return "bg-yellow-400 text-slate-900";
  return "bg-emerald-600";
}

function urgencyLabel(units: number, threshold = 5): string {
  if (units === 0) return "Critical";
  if (units < threshold) return "Low";
  return "OK";
}

function urgencyBadgeClass(units: number, threshold = 5): string {
  if (units === 0) return "bg-red-500/20 text-red-400 border border-red-500/40";
  if (units < threshold) return "bg-amber-500/20 text-amber-400 border border-amber-500/40";
  return "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40";
}

// -----------------------------------------------------------------------
// Sub-component: Bank Summary Card
// -----------------------------------------------------------------------
function BankCard({
  bank,
  isSelected,
  onClick,
}: {
  bank: BloodBank;
  isSelected: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`w-full text-left p-4 rounded-xl border transition-all duration-200 group hover:scale-[1.02] ${
        isSelected
          ? "bg-rose-600/20 border-rose-500 shadow-lg shadow-rose-900/30"
          : "bg-slate-800/60 border-slate-700 hover:border-slate-500"
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="font-semibold text-white truncate text-sm">{bank.name}</p>
          <p className="text-xs text-slate-400 truncate mt-0.5">{bank.city}</p>
        </div>
        <span
          className={`shrink-0 text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wide ${urgencyBadgeClass(bank.available_units)}`}
        >
          {urgencyLabel(bank.available_units)}
        </span>
      </div>
      <div className="mt-3 flex items-center gap-4 text-xs">
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block" />
          <span className="text-slate-300">{bank.available_units} available</span>
        </div>
        {bank.expiring_soon > 0 && (
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-amber-500 inline-block animate-pulse" />
            <span className="text-amber-400">{bank.expiring_soon} expiring soon</span>
          </div>
        )}
      </div>
    </button>
  );
}

// -----------------------------------------------------------------------
// Sub-component: Stock Matrix Cell
// -----------------------------------------------------------------------
function MatrixCell({
  units,
  earliestExpiry,
}: {
  units: number;
  earliestExpiry: string | null;
}) {
  const daysToExpiry = earliestExpiry
    ? Math.ceil(
        (new Date(earliestExpiry).getTime() - Date.now()) / (1000 * 60 * 60 * 24)
      )
    : undefined;

  const bg = units === 0 ? "bg-slate-800 text-slate-600" : expiryColor(daysToExpiry);

  return (
    <div
      className={`${bg} rounded-lg p-3 flex flex-col items-center justify-center min-h-[72px] transition-all duration-300 hover:scale-105 cursor-default`}
      title={
        earliestExpiry
          ? `Earliest expiry: ${earliestExpiry} (${daysToExpiry}d)`
          : "No available units"
      }
    >
      <span className="text-2xl font-bold leading-none">{units}</span>
      {daysToExpiry !== undefined && units > 0 && (
        <span className="text-[10px] mt-1 opacity-80">{daysToExpiry}d left</span>
      )}
    </div>
  );
}

// -----------------------------------------------------------------------
// Main InventoryDashboard component
// -----------------------------------------------------------------------
export default function InventoryDashboard() {
  const queryClient = useQueryClient();
  const [selectedBankId, setSelectedBankId] = useState<number | null>(null);
  const [sweepResult, setSweepResult] = useState<string | null>(null);

  // Queries
  const { data: banks = [], isLoading: banksLoading } = useQuery({
    queryKey: ["banks"],
    queryFn: fetchAllBanks,
  });

  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ["inventory-summary", selectedBankId],
    queryFn: () => fetchGlobalSummary(selectedBankId ?? undefined),
  });

  // Expiry sweep mutation
  const sweepMutation = useMutation({
    mutationFn: runExpirySweep,
    onSuccess: (result) => {
      setSweepResult(
        result.swept_count === 0
          ? "✓ No units needed sweeping — inventory is fresh."
          : `✓ Swept ${result.swept_count} expired unit(s) to EXPIRED status.`
      );
      queryClient.invalidateQueries({ queryKey: ["banks"] });
      queryClient.invalidateQueries({ queryKey: ["inventory-summary"] });
    },
  });

  // Build the matrix for the selected/global bank
  const allCells = summary?.banks.flatMap((b) => b.matrix) ?? [];
  const matrixMap = new Map(
    allCells.map((c) => [`${c.blood_group}::${c.component_type}`, c])
  );

  const lowStockAlerts = summary?.low_stock_alerts ?? [];

  return (
    <div className="min-h-screen bg-slate-950 text-white p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <span className="text-rose-500">🩸</span> Cold Storage Inventory
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Real-time blood unit availability across all blood banks
          </p>
        </div>
        <button
          id="btn-expiry-sweep"
          onClick={() => sweepMutation.mutate()}
          disabled={sweepMutation.isPending}
          className="flex items-center gap-2 bg-rose-600 hover:bg-rose-700 disabled:opacity-50 text-white text-sm font-semibold px-4 py-2 rounded-lg transition-colors duration-200 shadow-lg shadow-rose-900/40"
        >
          {sweepMutation.isPending ? (
            <>
              <span className="animate-spin">⟳</span> Running sweep...
            </>
          ) : (
            <>🗑 Run Expiry Sweep</>
          )}
        </button>
      </div>

      {/* Sweep result banner */}
      {sweepResult && (
        <div className="bg-slate-800 border border-slate-600 rounded-lg px-4 py-3 text-sm text-emerald-400 flex items-center justify-between">
          <span>{sweepResult}</span>
          <button
            onClick={() => setSweepResult(null)}
            className="text-slate-500 hover:text-white ml-4"
          >
            ✕
          </button>
        </div>
      )}

      {/* Low-stock alerts */}
      {lowStockAlerts.length > 0 && (
        <div className="bg-amber-900/20 border border-amber-700/40 rounded-xl p-4">
          <p className="text-amber-400 font-semibold text-sm mb-2">
            ⚠ Low Stock Alerts ({lowStockAlerts.length} group{lowStockAlerts.length > 1 ? "s" : ""})
          </p>
          <div className="flex flex-wrap gap-2">
            {lowStockAlerts.map((c, i) => (
              <span
                key={i}
                className="bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs px-3 py-1 rounded-full"
              >
                {c.blood_group} {COMPONENT_LABELS[c.component_type]} — {c.available_units} unit{c.available_units !== 1 ? "s" : ""}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* ---- Left Column: Bank List ---- */}
        <div className="lg:col-span-1 space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">
              Blood Banks
            </h2>
            <span className="text-xs text-slate-500">{banks.length} registered</span>
          </div>

          {/* "All Banks" option */}
          <button
            onClick={() => setSelectedBankId(null)}
            className={`w-full text-left p-3 rounded-xl border text-sm font-medium transition-all ${
              selectedBankId === null
                ? "bg-slate-700 border-slate-500 text-white"
                : "bg-slate-800/40 border-slate-700 text-slate-400 hover:border-slate-500"
            }`}
          >
            🏥 All Banks — Global View
          </button>

          {banksLoading ? (
            <div className="space-y-2">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="h-20 rounded-xl bg-slate-800 animate-pulse" />
              ))}
            </div>
          ) : (
            <div className="space-y-2 max-h-[60vh] overflow-y-auto pr-1">
              {banks.map((bank) => (
                <BankCard
                  key={bank.bank_id}
                  bank={bank}
                  isSelected={selectedBankId === bank.bank_id}
                  onClick={() =>
                    setSelectedBankId((prev) =>
                      prev === bank.bank_id ? null : bank.bank_id
                    )
                  }
                />
              ))}
            </div>
          )}
        </div>

        {/* ---- Right Column: Stock Matrix ---- */}
        <div className="lg:col-span-3 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">
              Blood Group × Component Matrix
            </h2>
            <div className="flex items-center gap-3 text-[11px] text-slate-500">
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-600 inline-block" />
                Good
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-yellow-400 inline-block" />
                Exp &lt;14d
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-amber-500 inline-block" />
                Exp &lt;7d
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-red-600 inline-block" />
                Exp &lt;3d
              </span>
            </div>
          </div>

          {summaryLoading ? (
            <div className="grid grid-cols-5 gap-2 animate-pulse">
              {[...Array(45)].map((_, i) => (
                <div key={i} className="h-[72px] rounded-lg bg-slate-800" />
              ))}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full border-separate border-spacing-2 min-w-[540px]">
                <thead>
                  <tr>
                    <th className="text-left text-xs text-slate-500 font-medium py-1 px-2 w-16">
                      Group
                    </th>
                    {COMPONENTS.map((c) => (
                      <th
                        key={c}
                        className="text-center text-xs text-slate-400 font-medium py-1 px-2"
                      >
                        {COMPONENT_LABELS[c]}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {BLOOD_GROUPS.map((group) => (
                    <tr key={group}>
                      <td className="text-center">
                        <span className="inline-flex items-center justify-center w-10 h-10 rounded-full bg-rose-700/30 border border-rose-600/40 text-rose-300 font-bold text-sm">
                          {group}
                        </span>
                      </td>
                      {COMPONENTS.map((component) => {
                        const cell = matrixMap.get(`${group}::${component}`);
                        return (
                          <td key={component} className="text-white">
                            <MatrixCell
                              units={cell?.available_units ?? 0}
                              earliestExpiry={cell?.earliest_expiry ?? null}
                            />
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Total summary strip */}
          {summary && (
            <div className="flex flex-wrap gap-4 bg-slate-800/50 rounded-xl px-5 py-3 border border-slate-700">
              <div className="text-sm">
                <span className="text-slate-400">Total Available: </span>
                <span className="text-emerald-400 font-bold">
                  {summary.total_available.toLocaleString()} units
                </span>
              </div>
              {selectedBankId !== null && (
                <div className="text-sm">
                  <span className="text-slate-400">Viewing: </span>
                  <span className="text-white font-medium">
                    {banks.find((b) => b.bank_id === selectedBankId)?.name}
                  </span>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
