/**
 * types/index.ts
 * ==============
 * TypeScript interfaces that mirror the Pydantic schemas exactly.
 * All frontend pages import types from here — never re-define inline.
 */

// ------------------------------------------------------------------
// Enums (mirror Python core/enums.py)
// ------------------------------------------------------------------

export type BloodGroup = "A+" | "A-" | "B+" | "B-" | "AB+" | "AB-" | "O+" | "O-";

export type ComponentType = "WHOLE_BLOOD" | "RBC" | "PLATELETS" | "PLASMA";

export type UnitStatus = "AVAILABLE" | "RESERVED" | "ISSUED" | "EXPIRED" | "DISCARDED";

export type UrgencyLevel = "ROUTINE" | "URGENT" | "EMERGENCY";

export type RequestStatus = "PENDING" | "PARTIALLY_FULFILLED" | "FULFILLED" | "CANCELLED";

export type UserRole = "ADMIN" | "BANK_STAFF" | "HOSPITAL_STAFF" | "DONOR";

// ------------------------------------------------------------------
// Blood Bank
// ------------------------------------------------------------------

export interface BloodBank {
  bank_id: number;
  name: string;
  address: string;
  city: string;
  contact: string;
  email: string | null;
  created_at: string; // ISO datetime string
  available_units: number;
  expiring_soon: number;
}

export interface BloodBankCreate {
  name: string;
  address: string;
  city: string;
  contact: string;
  email?: string;
}

export interface BloodBankUpdate {
  name?: string;
  address?: string;
  city?: string;
  contact?: string;
  email?: string;
}

// ------------------------------------------------------------------
// Blood Unit
// ------------------------------------------------------------------

export interface BloodUnit {
  bank_id: number;
  unit_id: number;
  donor_id: number;
  volume_ml: number;
  blood_group: BloodGroup;
  component_type: ComponentType;
  donation_date: string;      // ISO date string
  collection_date: string;
  expiry_date: string;
  status: UnitStatus;
  discard_reason: string | null;
  created_at: string;
  days_to_expiry: number;     // Injected by service layer
}

export interface DiscardUnitRequest {
  reason: string;
}

// ------------------------------------------------------------------
// Inventory Summary / Stock Matrix
// ------------------------------------------------------------------

export interface StockCell {
  blood_group: BloodGroup;
  component_type: ComponentType;
  available_units: number;
  earliest_expiry: string | null;
}

export interface BankInventorySummary {
  bank_id: number;
  bank_name: string;
  matrix: StockCell[];
}

export interface GlobalInventorySummary {
  banks: BankInventorySummary[];
  total_available: number;
  low_stock_alerts: StockCell[];
}

export interface ExpirySweepResult {
  swept_count: number;
  expired_unit_ids: { bank_id: number; unit_id: number }[];
}

// ------------------------------------------------------------------
// Donor (stub — Person 1 will expand)
// ------------------------------------------------------------------
export interface Donor {
  donor_id: number;
  name: string;
  blood_group: BloodGroup;
  phone: string;
  email: string | null;
  dob: string;
  gender: "MALE" | "FEMALE" | "OTHER";
  last_donation_date: string | null;
  created_at: string;
}

// ------------------------------------------------------------------
// Hospital & Recipient (stub — Person 3 will expand)
// ------------------------------------------------------------------
export interface Hospital {
  hospital_id: number;
  name: string;
  address: string;
  city: string;
  contact: string;
  email: string | null;
}

export interface Recipient {
  recipient_id: number;
  name: string;
  age: number;
  gender: "MALE" | "FEMALE" | "OTHER";
  blood_group: BloodGroup;
  hospital_id: number | null;
}

// ------------------------------------------------------------------
// Request (stub — Person 3 will expand)
// ------------------------------------------------------------------
export interface BloodRequest {
  request_id: number;
  hospital_id: number;
  recipient_id: number;
  blood_group: BloodGroup;
  component_type: ComponentType;
  quantity: number;
  urgency: UrgencyLevel;
  request_date: string;
  status: RequestStatus;
  notes: string | null;
}

// ------------------------------------------------------------------
// Issue (stub — Person 4 will expand)
// ------------------------------------------------------------------
export interface Issue {
  issue_id: number;
  request_id: number;
  bank_id: number;
  unit_id: number;
  issue_date: string;
  quantity_issued: number;
  notes: string | null;
}

// ------------------------------------------------------------------
// Auth (stub — Person 4 will expand)
// ------------------------------------------------------------------
export interface AuthToken {
  access_token: string;
  token_type: string;
  role: UserRole;
}

export interface CurrentUser {
  user_id: number;
  username: string;
  email: string;
  full_name: string;
  role: UserRole;
}
