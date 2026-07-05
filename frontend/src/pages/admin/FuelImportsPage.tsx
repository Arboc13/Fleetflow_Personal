import { useEffect, useRef, useState } from "react";
import { FuelApi } from "../../api/resources";
import type { ImportBatch, ImportRowError } from "../../api/types";
import Modal from "../../components/Modal";
import {
  Badge,
  Button,
  Card,
  Empty,
  ErrorText,
  Loading,
  Table,
} from "../../components/ui";
import { useLoad } from "../../hooks/useLoad";
import { fmtDateTime } from "../../lib/fmt";

function errorRows(batch: ImportBatch): ImportRowError[] {
  return Array.isArray(batch.error_report) ? batch.error_report : [];
}

function ErrorReportModal({ batch, onClose }: { batch: ImportBatch; onClose: () => void }) {
  const rows = errorRows(batch);
  return (
    <Modal title={`Rejected rows — ${batch.filename}`} open onClose={onClose}>
      {rows.length === 0 ? (
        <Empty>No rejected rows.</Empty>
      ) : (
        <div className="max-h-96 overflow-y-auto">
          <Table headers={["Row", "Problem"]}>
            {rows.map((r, i) => (
              <tr key={i}>
                <td className="px-3 py-2 text-slate-500">{r.row ?? "?"}</td>
                <td className="px-3 py-2">{r.error ?? JSON.stringify(r)}</td>
              </tr>
            ))}
          </Table>
        </div>
      )}
    </Modal>
  );
}

export default function FuelImportsPage() {
  const batches = useLoad(() => FuelApi.batches());
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [detail, setDetail] = useState<ImportBatch | null>(null);
  const fileInput = useRef<HTMLInputElement>(null);

  // While any batch is pending/processing, poll so the row counts move
  // without a manual refresh (the parse runs as a background task).
  const hasRunning = (batches.data ?? []).some(
    (b) => b.status === "pending" || b.status === "processing",
  );
  useEffect(() => {
    if (!hasRunning) return;
    const timer = setInterval(batches.reload, 2000);
    return () => clearInterval(timer);
  }, [hasRunning, batches.reload]);

  async function handleUpload(file: File) {
    setUploading(true);
    setUploadError(null);
    try {
      await FuelApi.upload(file);
      batches.reload();
    } catch (err) {
      setUploadError((err as Error).message);
    } finally {
      setUploading(false);
      if (fileInput.current) fileInput.current.value = "";
    }
  }

  return (
    <>
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">Fuel imports</h1>
        <div>
          <input
            ref={fileInput}
            type="file"
            accept=".csv,.xlsx,.xls"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) handleUpload(file);
            }}
          />
          <Button onClick={() => fileInput.current?.click()} disabled={uploading}>
            {uploading ? "Uploading…" : "Upload CSV / Excel"}
          </Button>
        </div>
      </div>
      <ErrorText message={uploadError ?? batches.error} />

      <Card title="Import batches">
        {batches.loading && !batches.data ? (
          <Loading />
        ) : (batches.data ?? []).length === 0 ? (
          <Empty>No imports yet — upload a fuel provider file to start.</Empty>
        ) : (
          <Table headers={["File", "Uploaded", "Status", "Rows", "Imported", "Rejected", ""]}>
            {(batches.data ?? []).map((b) => (
              <tr key={b.id}>
                <td className="px-3 py-2 font-medium">{b.filename}</td>
                <td className="px-3 py-2">{fmtDateTime(b.created_at)}</td>
                <td className="px-3 py-2">
                  <Badge value={b.status} />
                </td>
                <td className="px-3 py-2">{b.total_rows}</td>
                <td className="px-3 py-2 text-green-700">{b.imported_rows}</td>
                <td className="px-3 py-2 text-red-700">{b.rejected_rows}</td>
                <td className="px-3 py-2 text-right">
                  {(b.rejected_rows > 0 || b.status === "failed") && (
                    <Button variant="ghost" onClick={() => setDetail(b)}>
                      Error report
                    </Button>
                  )}
                </td>
              </tr>
            ))}
          </Table>
        )}
      </Card>

      <SuspectTransactions />

      {detail && <ErrorReportModal batch={detail} onClose={() => setDetail(null)} />}
    </>
  );
}

function SuspectTransactions() {
  const { data, loading } = useLoad(() => FuelApi.transactions({ suspect_only: true }));
  return (
    <Card title="Suspect transactions (over tank capacity or inconsistent odometer)">
      {loading ? (
        <Loading />
      ) : (data ?? []).length === 0 ? (
        <Empty>No suspect transactions. 🎉</Empty>
      ) : (
        <Table headers={["Vehicle", "Date", "Liters", "Odometer", "Reason"]}>
          {(data ?? []).map((tx) => (
            <tr key={tx.id} className="bg-red-50">
              <td className="px-3 py-2">#{tx.vehicle_id}</td>
              <td className="px-3 py-2">{fmtDateTime(tx.occurred_at)}</td>
              <td className="px-3 py-2">{tx.liters.toFixed(2)} L</td>
              <td className="px-3 py-2">
                {tx.odometer_reported?.toLocaleString("ro-RO") ?? "—"}
              </td>
              <td className="px-3 py-2 text-red-700">{tx.suspect_reason}</td>
            </tr>
          ))}
        </Table>
      )}
    </Card>
  );
}
