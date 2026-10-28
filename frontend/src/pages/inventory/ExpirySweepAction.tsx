import React, { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { runExpirySweep } from "../../api/inventory";
import type { ExpirySweepResult } from "../../types";

// -----------------------------------------------------------------------
// Standalone Expiry Sweep Action card — can be embedded in any page
// or used as a standalone admin tool card.
// -----------------------------------------------------------------------

export default function ExpirySweepAction() {
  const queryClient = useQueryClient();
  const [result, setResult] = useState<ExpirySweepResult | null>(null);

  const sweepMutation = useMutation({
    mutationFn: runExpirySweep,
    onSuccess: (data) => {
      setResult(data);
      // Invalidate all inventory-related queries so the matrix refreshes
      queryClient.invalidateQueries({ queryKey: ["banks"] });
      queryClient.invalidateQueries({ queryKey: ["inventory-summary"] });
    },
  });

  return (
    <div className="bg-slate-900 border border-slate-700 rounded-2xl p-6 max-w-lg">
      {/* Header */}
      <div className="flex items-center gap-3 mb-4">
        <div className="w-10 h-10 rounded-xl bg-rose-600/20 border border-rose-600/30 flex items-center justify-center text-lg">
          🗑
        </div>
        <div>
          <h3 className="text-white font-bold text-base">Expiry Sweep</h3>
          <p className="text-slate-400 text-xs mt-0.5">
            Marks all past-expiry AVAILABLE units as EXPIRED
          </p>
        </div>
      </div>

      {/* Info panel */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4 mb-5 text-sm text-slate-300 space-y-2">
        <p className="flex gap-2">
          <span className="text-slate-500">→</span>
          Scans every AVAILABLE blood unit for today's date.
        </p>
        <p className="flex gap-2">
          <span className="text-slate-500">→</span>
          Units with <code className="text-amber-400">expiry_date &lt; TODAY</code> are
          transitioned to <code className="text-rose-400">EXPIRED</code> status.
        </p>
        <p className="flex gap-2">
          <span className="text-slate-500">→</span>
          Safe to run multiple times — already-expired units are not re-processed.
        </p>
        <p className="flex gap-2">
          <span className="text-slate-500">→</span>
          Backed by the MySQL trigger{" "}
          <code className="text-sky-400">trg_after_issue_insert</code> for
          atomicity.
        </p>
      </div>

      {/* Action button */}
      <button
        id="btn-run-expiry-sweep"
        onClick={() => {
          setResult(null);
          sweepMutation.mutate();
        }}
        disabled={sweepMutation.isPending}
        className="w-full bg-rose-600 hover:bg-rose-700 disabled:opacity-50 text-white font-semibold py-3 rounded-xl text-sm transition-all duration-200 flex items-center justify-center gap-2 shadow-lg shadow-rose-900/30 hover:shadow-rose-900/50"
      >
        {sweepMutation.isPending ? (
          <>
            <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            Running Expiry Sweep...
          </>
        ) : (
          "🗑 Run Expiry Sweep Now"
        )}
      </button>

      {/* Error state */}
      {sweepMutation.isError && (
        <div className="mt-4 bg-red-900/20 border border-red-700/40 rounded-xl p-4 text-sm text-red-400">
          ❌ Sweep failed. Please check the server logs.
        </div>
      )}

      {/* Success result */}
      {result && !sweepMutation.isPending && (
        <div className="mt-4 bg-emerald-900/20 border border-emerald-700/40 rounded-xl p-4">
          <p className="text-emerald-400 font-semibold text-sm mb-2">
            ✓ Sweep Complete
          </p>
          {result.swept_count === 0 ? (
            <p className="text-slate-400 text-sm">
              All AVAILABLE units are within their expiry date. Nothing to sweep.
            </p>
          ) : (
            <>
              <p className="text-slate-300 text-sm mb-3">
                <span className="text-white font-bold text-lg">{result.swept_count}</span>{" "}
                unit{result.swept_count !== 1 ? "s" : ""} transitioned to{" "}
                <span className="text-rose-400">EXPIRED</span>.
              </p>
              {result.expired_unit_ids.length > 0 && (
                <div className="max-h-32 overflow-y-auto space-y-1">
                  {result.expired_unit_ids.map(({ bank_id, unit_id }) => (
                    <div
                      key={`${bank_id}-${unit_id}`}
                      className="flex gap-3 text-xs text-slate-400 bg-slate-800 px-3 py-1.5 rounded-lg"
                    >
                      <span>Bank <span className="text-slate-300">#{bank_id}</span></span>
                      <span>Unit <span className="text-slate-300">#{unit_id}</span></span>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}
