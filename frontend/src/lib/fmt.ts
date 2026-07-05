// Display formatting. The backend stores datetimes in UTC; users see local time.

export function fmtDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("ro-RO");
}

export function fmtDateTime(iso: string | null | undefined): string {
  if (!iso) return "—";
  // Naive UTC timestamps from the API lack a zone suffix; add it so the
  // Date is parsed as UTC, then rendered in the viewer's local time.
  const value = /Z|[+-]\d\d:?\d\d$/.test(iso) ? iso : `${iso}Z`;
  return new Date(value).toLocaleString("ro-RO", {
    dateStyle: "short",
    timeStyle: "short",
  });
}

export function fmtMoney(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return value.toLocaleString("ro-RO", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + " lei";
}

export function fmtKm(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return value.toLocaleString("ro-RO") + " km";
}

/** Value for <input type="datetime-local"> from an ISO/UTC timestamp. */
export function toLocalInput(iso?: string | null): string {
  const d = iso ? new Date(/Z|[+-]\d\d:?\d\d$/.test(iso) ? iso : `${iso}Z`) : new Date();
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

/** Convert a datetime-local input value (local time) to UTC ISO for the API. */
export function fromLocalInput(value: string): string {
  return new Date(value).toISOString();
}

/** Today as YYYY-MM-DD (for <input type="date"> defaults). */
export function todayISO(offsetDays = 0): string {
  const d = new Date();
  d.setDate(d.getDate() + offsetDays);
  return d.toISOString().slice(0, 10);
}
