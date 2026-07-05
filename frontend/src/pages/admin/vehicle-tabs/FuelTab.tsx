import { useState } from "react";
import { FuelApi } from "../../../api/resources";
import { Card, Empty, Loading, Table } from "../../../components/ui";
import { useLoad } from "../../../hooks/useLoad";
import { fmtDateTime, fmtKm, fmtMoney } from "../../../lib/fmt";

export default function FuelTab({ vehicleId }: { vehicleId: number }) {
  const [suspectOnly, setSuspectOnly] = useState(false);
  const { data, loading } = useLoad(
    () => FuelApi.transactions({ vehicle_id: vehicleId, suspect_only: suspectOnly }),
    [vehicleId, suspectOnly],
  );

  return (
    <Card
      title="Fuel transactions"
      actions={
        <label className="flex items-center gap-2 text-sm text-slate-600">
          <input
            type="checkbox"
            checked={suspectOnly}
            onChange={(e) => setSuspectOnly(e.target.checked)}
          />
          Suspect only
        </label>
      }
    >
      {loading ? (
        <Loading />
      ) : (data ?? []).length === 0 ? (
        <Empty>No fuel transactions{suspectOnly ? " flagged as suspect" : ""}.</Empty>
      ) : (
        <Table headers={["Date", "Liters", "Price", "Odometer", "Station", "Flag"]}>
          {(data ?? []).map((tx) => (
            <tr key={tx.id} className={tx.is_suspect ? "bg-red-50" : undefined}>
              <td className="px-3 py-2">{fmtDateTime(tx.occurred_at)}</td>
              <td className="px-3 py-2">{tx.liters.toFixed(2)} L</td>
              <td className="px-3 py-2">{fmtMoney(tx.price)}</td>
              <td className="px-3 py-2">{fmtKm(tx.odometer_reported)}</td>
              <td className="px-3 py-2">{tx.station ?? "—"}</td>
              <td className="px-3 py-2 text-xs text-red-700">{tx.suspect_reason ?? ""}</td>
            </tr>
          ))}
        </Table>
      )}
    </Card>
  );
}
