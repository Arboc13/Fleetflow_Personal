import type {
  ButtonHTMLAttributes,
  InputHTMLAttributes,
  ReactNode,
  SelectHTMLAttributes,
  TextareaHTMLAttributes,
} from "react";

// Small shared building blocks so pages stay declarative. Tailwind-only,
// no component library.

export function cls(...parts: (string | false | undefined)[]): string {
  return parts.filter(Boolean).join(" ");
}

type ButtonVariant = "primary" | "secondary" | "danger" | "ghost";

const BUTTON_STYLES: Record<ButtonVariant, string> = {
  primary: "bg-sky-600 text-white hover:bg-sky-700 disabled:bg-sky-300",
  secondary:
    "bg-white text-slate-700 border border-slate-300 hover:bg-slate-50 disabled:text-slate-400",
  danger: "bg-red-600 text-white hover:bg-red-700 disabled:bg-red-300",
  ghost: "text-sky-700 hover:bg-sky-50 disabled:text-slate-400",
};

export function Button({
  variant = "primary",
  className,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: ButtonVariant }) {
  return (
    <button
      type="button"
      className={cls(
        "rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
        BUTTON_STYLES[variant],
        className,
      )}
      {...props}
    />
  );
}

export function Input(props: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...props}
      className={cls(
        "w-full rounded-md border border-slate-300 px-2.5 py-1.5 text-sm",
        "focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500",
        props.className,
      )}
    />
  );
}

export function Select(props: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      {...props}
      className={cls(
        "w-full rounded-md border border-slate-300 bg-white px-2.5 py-1.5 text-sm",
        "focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500",
        props.className,
      )}
    />
  );
}

export function Textarea(props: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      rows={3}
      {...props}
      className={cls(
        "w-full rounded-md border border-slate-300 px-2.5 py-1.5 text-sm",
        "focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500",
        props.className,
      )}
    />
  );
}

export function Field({
  label,
  children,
  hint,
  error,
}: {
  label: string;
  children: ReactNode;
  hint?: string;
  error?: string | null;
}) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm font-medium text-slate-700">{label}</span>
      {children}
      {/* Live, non-blocking feedback (NFR-3): shown while typing, does not
          prevent submitting — the backend re-validates anyway. */}
      {error ? (
        <span className="mt-1 block text-xs text-red-600">{error}</span>
      ) : hint ? (
        <span className="mt-1 block text-xs text-slate-500">{hint}</span>
      ) : null}
    </label>
  );
}

export function Card({ title, actions, children }: { title?: string; actions?: ReactNode; children: ReactNode }) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      {(title || actions) && (
        <div className="mb-3 flex items-center justify-between">
          {title && <h2 className="text-sm font-semibold text-slate-800">{title}</h2>}
          {actions}
        </div>
      )}
      {children}
    </section>
  );
}

const BADGE_COLORS: Record<string, string> = {
  // vehicle status
  active: "bg-green-100 text-green-800",
  in_service: "bg-yellow-100 text-yellow-800",
  unavailable: "bg-slate-200 text-slate-600",
  // lifecycle
  draft: "bg-yellow-100 text-yellow-800",
  closed: "bg-slate-200 text-slate-600",
  ended: "bg-slate-200 text-slate-600",
  // imports
  pending: "bg-slate-100 text-slate-600",
  processing: "bg-sky-100 text-sky-800",
  completed: "bg-green-100 text-green-800",
  failed: "bg-red-100 text-red-800",
  // notification severity (red/yellow indicators)
  warning: "bg-yellow-100 text-yellow-800",
  critical: "bg-red-100 text-red-800",
};

export function Badge({ value }: { value: string }) {
  return (
    <span
      className={cls(
        "inline-block rounded-full px-2 py-0.5 text-xs font-medium",
        BADGE_COLORS[value] ?? "bg-slate-100 text-slate-600",
      )}
    >
      {value.replace("_", " ")}
    </span>
  );
}

export function ErrorText({ message }: { message: string | null }) {
  if (!message) return null;
  return (
    <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{message}</p>
  );
}

export function Loading() {
  return <p className="py-6 text-center text-sm text-slate-500">Loading…</p>;
}

export function Empty({ children = "Nothing here yet." }: { children?: ReactNode }) {
  return <p className="py-6 text-center text-sm text-slate-400">{children}</p>;
}

/** Plain data table; pass rows already rendered as <tr>. */
export function Table({ headers, children }: { headers: string[]; children: ReactNode }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
            {headers.map((h) => (
              <th key={h} className="px-3 py-2 font-medium">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">{children}</tbody>
      </table>
    </div>
  );
}
