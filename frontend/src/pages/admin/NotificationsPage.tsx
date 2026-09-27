import { NotificationsApi } from "../../api/resources";
import { Badge, Button, Card, Empty, ErrorText, Loading, cls } from "../../components/ui";
import { useLoad } from "../../hooks/useLoad";
import { fmtDateTime } from "../../lib/fmt";

export default function NotificationsPage() {
  const { data, loading, error, reload } = useLoad(() => NotificationsApi.list());

  async function markRead(id: number) {
    await NotificationsApi.markRead(id);
    reload();
  }

  async function markAll() {
    await NotificationsApi.markAllRead();
    reload();
  }

  const items = data ?? [];

  return (
    <>
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">Alerts & notifications</h1>
        {items.some((n) => !n.read_at) && (
          <Button variant="secondary" onClick={markAll}>
            Mark all read
          </Button>
        )}
      </div>
      <ErrorText message={error} />
      <Card>
        {loading ? (
          <Loading />
        ) : items.length === 0 ? (
          <Empty>No notifications.</Empty>
        ) : (
          <ul className="divide-y divide-slate-100">
            {items.map((n) => (
              <li
                key={n.id}
                className={cls(
                  "flex items-center gap-3 py-2.5 text-sm",
                  !!n.read_at && "opacity-60",
                )}
              >
                <Badge value={n.severity} />
                <div className="flex-1">
                  <p>{n.message}</p>
                  <p className="text-xs text-slate-400">
                    {n.type} · {fmtDateTime(n.created_at)}
                  </p>
                </div>
                {!n.read_at && (
                  <Button variant="ghost" onClick={() => markRead(n.id)}>
                    Mark read
                  </Button>
                )}
              </li>
            ))}
          </ul>
        )}
      </Card>
    </>
  );
}
