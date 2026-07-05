// Mirrors the backend's Pydantic schemas (backend/app/schemas/*).
// Dates are ISO strings on the wire: `YYYY-MM-DD` for dates,
// `YYYY-MM-DDTHH:MM:SS` for datetimes.

export type Role = "admin" | "fleet_manager" | "driver";

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: Role;
  is_active: boolean;
}

export type FuelType = "petrol" | "diesel" | "electric" | "hybrid" | "lpg";
export type VehicleStatus = "active" | "in_service" | "unavailable";

export interface Vehicle {
  id: number;
  plate: string;
  vin: string;
  make: string;
  model: string;
  year: number;
  fuel_type: FuelType;
  tank_capacity_l: number;
  fuel_card_number: string | null;
  status: VehicleStatus;
  current_km: number;
}

export interface VehicleCreate {
  plate: string;
  vin: string;
  make: string;
  model: string;
  year: number;
  fuel_type: FuelType;
  tank_capacity_l: number;
  fuel_card_number?: string | null;
  status?: VehicleStatus;
  current_km?: number;
}

export type VehicleUpdate = Partial<Omit<VehicleCreate, "plate" | "vin">>;

export interface Driver {
  id: number;
  user_id: number;
  email: string;
  full_name: string;
  phone: string | null;
  cnp_masked: string;
  license_number: string;
  license_series: string | null;
  license_category: string;
  license_expiry: string;
  is_active: boolean;
}

export interface DriverCreate {
  email: string;
  full_name: string;
  password: string;
  cnp: string;
  phone?: string | null;
  license_number: string;
  license_series?: string | null;
  license_category: string;
  license_expiry: string;
}

export interface DriverUpdate {
  phone?: string | null;
  license_number?: string;
  license_series?: string | null;
  license_category?: string;
  license_expiry?: string;
  cnp?: string;
}

export type AllocationType = "permanent" | "trip";
export type AllocationStatus = "active" | "ended";

export interface Allocation {
  id: number;
  vehicle_id: number;
  driver_id: number;
  start_at: string;
  end_at: string | null;
  type: AllocationType;
  status: AllocationStatus;
}

export interface AllocationCreate {
  vehicle_id: number;
  driver_id: number;
  start_at: string;
  end_at?: string | null;
  type: AllocationType;
}

export type HandoverDirection = "handover" | "return";
export type HandoverStatus = "draft" | "closed";

export interface HandoverReport {
  id: number;
  allocation_id: number;
  direction: HandoverDirection;
  km: number;
  fuel_level_pct: number;
  visual_observations: string | null;
  cleanliness: string | null;
  status: HandoverStatus;
}

export interface HandoverReportCreate {
  allocation_id: number;
  direction: HandoverDirection;
  km: number;
  fuel_level_pct: number;
  visual_observations?: string | null;
  cleanliness?: string | null;
}

export type DocumentType = "RCA" | "CASCO" | "ITP" | "Rovinieta";

export interface VehicleDocument {
  id: number;
  vehicle_id: number;
  type: DocumentType;
  series_number: string;
  issuer: string | null;
  cost: number;
  issue_date: string;
  expiry_date: string;
}

export interface DocumentCreate {
  vehicle_id: number;
  type: DocumentType;
  series_number: string;
  issuer?: string | null;
  cost?: number;
  issue_date: string;
  expiry_date: string;
}

export interface ServiceRecord {
  id: number;
  vehicle_id: number;
  date: string;
  km_at_service: number;
  work_description: string;
  parts_replaced: string | null;
  cost: number;
}

export interface ServiceRecordCreate {
  vehicle_id: number;
  date: string;
  km_at_service: number;
  work_description: string;
  parts_replaced?: string | null;
  cost?: number;
}

export interface MaintenanceRule {
  id: number;
  vehicle_id: number;
  name: string;
  interval_km: number;
  interval_months: number;
  last_service_km: number;
  last_service_date: string;
}

export interface MaintenanceRuleCreate {
  vehicle_id: number;
  name?: string;
  interval_km: number;
  interval_months: number;
  last_service_km: number;
  last_service_date: string;
}

export type TripStatus = "draft" | "closed";

export interface TripSheet {
  id: number;
  vehicle_id: number;
  driver_id: number;
  departure_at: string;
  arrival_at: string | null;
  start_km: number;
  end_km: number | null;
  purpose: string | null;
  status: TripStatus;
}

export interface TripSheetCreate {
  vehicle_id: number;
  driver_id?: number; // omitted for drivers — the backend forces their own id
  departure_at: string;
  start_km: number;
  purpose?: string | null;
}

export type ImportStatus = "pending" | "processing" | "completed" | "failed";

export interface ImportBatch {
  id: number;
  filename: string;
  status: ImportStatus;
  total_rows: number;
  imported_rows: number;
  rejected_rows: number;
  error_report: ImportRowError[] | Record<string, unknown> | null;
  created_at: string;
}

export interface ImportRowError {
  row?: number;
  error?: string;
  [key: string]: unknown;
}

export interface FuelTransaction {
  id: number;
  vehicle_id: number;
  occurred_at: string;
  liters: number;
  price: number | null;
  odometer_reported: number | null;
  station: string | null;
  import_batch_id: number | null;
  is_suspect: boolean;
  suspect_reason: string | null;
}

export type Severity = "warning" | "critical";

export interface Notification {
  id: number;
  type: string;
  severity: Severity;
  message: string;
  entity_type: string | null;
  entity_id: number | null;
  read_at: string | null;
  created_at: string;
}

export interface VehicleTCORow {
  vehicle_id: number;
  plate: string;
  make: string;
  model: string;
  fuel_cost: number;
  service_cost: number;
  document_cost: number;
  total_cost: number;
  km_driven: number;
  cost_per_km: number | null;
  utilization_pct: number;
}

export interface FleetTotals {
  fuel_cost: number;
  service_cost: number;
  document_cost: number;
  total_cost: number;
  km_driven: number;
  cost_per_km: number | null;
  utilization_pct: number;
}

export interface TCOReport {
  date_from: string;
  date_to: string;
  rows: VehicleTCORow[];
  fleet: FleetTotals;
}
