import { download, request } from "./client";
import type {
  Allocation,
  AllocationCreate,
  Driver,
  DriverCreate,
  DriverUpdate,
  DocumentCreate,
  FuelTransaction,
  HandoverReport,
  HandoverReportCreate,
  ImportBatch,
  MaintenanceRule,
  MaintenanceRuleCreate,
  Notification,
  ServiceRecord,
  ServiceRecordCreate,
  TCOReport,
  TripSheet,
  TripSheetCreate,
  User,
  Vehicle,
  VehicleCreate,
  VehicleDocument,
  VehicleUpdate,
} from "./types";

export const AuthApi = {
  async login(email: string, password: string): Promise<string> {
    const form = new URLSearchParams({ username: email, password });
    const token = await request<{ access_token: string }>("/auth/login", {
      method: "POST",
      form,
    });
    return token.access_token;
  },
  me: () => request<User>("/auth/me"),
};

export const VehiclesApi = {
  list: () => request<Vehicle[]>("/vehicles"),
  get: (id: number) => request<Vehicle>(`/vehicles/${id}`),
  create: (data: VehicleCreate) =>
    request<Vehicle>("/vehicles", { method: "POST", body: data }),
  update: (id: number, data: VehicleUpdate) =>
    request<Vehicle>(`/vehicles/${id}`, { method: "PATCH", body: data }),
  remove: (id: number) => request<void>(`/vehicles/${id}`, { method: "DELETE" }),
};

export const DriversApi = {
  list: () => request<Driver[]>("/drivers"),
  create: (data: DriverCreate) =>
    request<Driver>("/drivers", { method: "POST", body: data }),
  update: (id: number, data: DriverUpdate) =>
    request<Driver>(`/drivers/${id}`, { method: "PATCH", body: data }),
  remove: (id: number) => request<void>(`/drivers/${id}`, { method: "DELETE" }),
};

export const AllocationsApi = {
  list: (filter?: { vehicle_id?: number; driver_id?: number }) =>
    request<Allocation[]>("/allocations", { query: filter }),
  create: (data: AllocationCreate) =>
    request<Allocation>("/allocations", { method: "POST", body: data }),
  update: (id: number, data: Partial<AllocationCreate>) =>
    request<Allocation>(`/allocations/${id}`, { method: "PATCH", body: data }),
  remove: (id: number) => request<void>(`/allocations/${id}`, { method: "DELETE" }),
};

export const HandoverApi = {
  list: (allocation_id?: number) =>
    request<HandoverReport[]>("/handover-reports", { query: { allocation_id } }),
  create: (data: HandoverReportCreate) =>
    request<HandoverReport>("/handover-reports", { method: "POST", body: data }),
  update: (id: number, data: Partial<Omit<HandoverReportCreate, "allocation_id" | "direction">>) =>
    request<HandoverReport>(`/handover-reports/${id}`, { method: "PATCH", body: data }),
  close: (id: number) =>
    request<HandoverReport>(`/handover-reports/${id}/close`, { method: "POST" }),
};

export const DocumentsApi = {
  list: (vehicle_id?: number) =>
    request<VehicleDocument[]>("/documents", { query: { vehicle_id } }),
  create: (data: DocumentCreate) =>
    request<VehicleDocument>("/documents", { method: "POST", body: data }),
  update: (id: number, data: Partial<DocumentCreate>) =>
    request<VehicleDocument>(`/documents/${id}`, { method: "PATCH", body: data }),
  remove: (id: number) => request<void>(`/documents/${id}`, { method: "DELETE" }),
};

export const ServiceRecordsApi = {
  list: (vehicle_id?: number) =>
    request<ServiceRecord[]>("/service-records", { query: { vehicle_id } }),
  create: (data: ServiceRecordCreate) =>
    request<ServiceRecord>("/service-records", { method: "POST", body: data }),
  update: (id: number, data: Partial<ServiceRecordCreate>) =>
    request<ServiceRecord>(`/service-records/${id}`, { method: "PATCH", body: data }),
  remove: (id: number) =>
    request<void>(`/service-records/${id}`, { method: "DELETE" }),
};

export const MaintenanceApi = {
  list: (vehicle_id?: number) =>
    request<MaintenanceRule[]>("/maintenance-rules", { query: { vehicle_id } }),
  create: (data: MaintenanceRuleCreate) =>
    request<MaintenanceRule>("/maintenance-rules", { method: "POST", body: data }),
  update: (id: number, data: Partial<MaintenanceRuleCreate>) =>
    request<MaintenanceRule>(`/maintenance-rules/${id}`, { method: "PATCH", body: data }),
  remove: (id: number) =>
    request<void>(`/maintenance-rules/${id}`, { method: "DELETE" }),
};

export const TripSheetsApi = {
  list: (filter?: { vehicle_id?: number; driver_id?: number; status_filter?: string }) =>
    request<TripSheet[]>("/trip-sheets", { query: filter }),
  create: (data: TripSheetCreate) =>
    request<TripSheet>("/trip-sheets", { method: "POST", body: data }),
  update: (id: number, data: Partial<Omit<TripSheetCreate, "vehicle_id" | "driver_id">>) =>
    request<TripSheet>(`/trip-sheets/${id}`, { method: "PATCH", body: data }),
  close: (id: number, arrival_at: string, end_km: number) =>
    request<TripSheet>(`/trip-sheets/${id}/close`, {
      method: "POST",
      body: { arrival_at, end_km },
    }),
  remove: (id: number) => request<void>(`/trip-sheets/${id}`, { method: "DELETE" }),
};

export const FuelApi = {
  upload(file: File): Promise<ImportBatch> {
    const form = new FormData();
    form.append("file", file);
    return request<ImportBatch>("/fuel-imports", { method: "POST", form });
  },
  batches: () => request<ImportBatch[]>("/fuel-imports"),
  batch: (id: number) => request<ImportBatch>(`/fuel-imports/${id}`),
  transactions: (filter?: {
    vehicle_id?: number;
    batch_id?: number;
    suspect_only?: boolean;
  }) => request<FuelTransaction[]>("/fuel-transactions", { query: filter }),
};

export const NotificationsApi = {
  list: (unread_only = false) =>
    request<Notification[]>("/notifications", { query: { unread_only } }),
  unreadCount: async () =>
    (await request<{ unread: number }>("/notifications/unread-count")).unread,
  markRead: (id: number) =>
    request<Notification>(`/notifications/${id}/read`, { method: "POST" }),
  markAllRead: () =>
    request<{ marked_read: number }>("/notifications/read-all", { method: "POST" }),
};

export const AlertsApi = {
  run: () => request<{ created: number }>("/alerts/run", { method: "POST" }),
};

export const ReportsApi = {
  tco: (date_from: string, date_to: string, vehicle_id?: number) =>
    request<TCOReport>("/reports/tco", { query: { date_from, date_to, vehicle_id } }),
  export: (date_from: string, date_to: string, format: "xlsx" | "pdf") =>
    download(
      "/reports/tco/export",
      { date_from, date_to, format },
      `tco_${date_from}_${date_to}.${format}`,
    ),
};
