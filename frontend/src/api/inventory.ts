/**
 * api/inventory.ts
 * ================
 * All API calls for blood banks and blood unit inventory.
 * Person 2 owns this file.
 */

import client from "./client";
import type {
  BloodBank,
  BloodBankCreate,
  BloodBankUpdate,
  BloodUnit,
  DiscardUnitRequest,
  ExpirySweepResult,
  GlobalInventorySummary,
  ComponentType,
  BloodGroup,
  UnitStatus,
} from "../types";

// -----------------------------------------------------------------------
// Blood Bank CRUD
// -----------------------------------------------------------------------

export const fetchAllBanks = async (): Promise<BloodBank[]> => {
  const { data } = await client.get<BloodBank[]>("/api/v1/banks");
  return data;
};

export const fetchBankById = async (bankId: number): Promise<BloodBank> => {
  const { data } = await client.get<BloodBank>(`/api/v1/banks/${bankId}`);
  return data;
};

export const createBank = async (payload: BloodBankCreate): Promise<BloodBank> => {
  const { data } = await client.post<BloodBank>("/api/v1/banks", payload);
  return data;
};

export const updateBank = async (
  bankId: number,
  payload: BloodBankUpdate
): Promise<BloodBank> => {
  const { data } = await client.put<BloodBank>(`/api/v1/banks/${bankId}`, payload);
  return data;
};

export const deleteBank = async (bankId: number): Promise<void> => {
  await client.delete(`/api/v1/banks/${bankId}`);
};

// -----------------------------------------------------------------------
// Inventory Queries
// -----------------------------------------------------------------------

export interface UnitFilters {
  blood_group?: BloodGroup;
  component_type?: ComponentType;
  status?: UnitStatus;
  expiring_within_days?: number;
  skip?: number;
  limit?: number;
}

export const fetchUnitsForBank = async (
  bankId: number,
  filters: UnitFilters = {}
): Promise<BloodUnit[]> => {
  const { data } = await client.get<BloodUnit[]>(
    `/api/v1/inventory/banks/${bankId}/units`,
    { params: filters }
  );
  return data;
};

export const fetchGlobalSummary = async (
  bankId?: number
): Promise<GlobalInventorySummary> => {
  const { data } = await client.get<GlobalInventorySummary>(
    "/api/v1/inventory/summary",
    { params: bankId !== undefined ? { bank_id: bankId } : {} }
  );
  return data;
};

export const fetchUnitById = async (
  bankId: number,
  unitId: number
): Promise<BloodUnit> => {
  const { data } = await client.get<BloodUnit>(
    `/api/v1/inventory/units/${bankId}/${unitId}`
  );
  return data;
};

export const runExpirySweep = async (): Promise<ExpirySweepResult> => {
  const { data } = await client.post<ExpirySweepResult>(
    "/api/v1/inventory/expire-sweep"
  );
  return data;
};

export const discardUnit = async (
  bankId: number,
  unitId: number,
  payload: DiscardUnitRequest
): Promise<BloodUnit> => {
  const { data } = await client.patch<BloodUnit>(
    `/api/v1/inventory/units/${bankId}/${unitId}/discard`,
    payload
  );
  return data;
};
