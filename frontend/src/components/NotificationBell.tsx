import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { NotificationsApi } from "../api/resources";

/** Bell with unread badge; refreshes every minute. Links to the alert list. */
export default function NotificationBell({ to }: { to: string }) {
  const [unread, setUnread] = useState(0);

  useEffect(() => {
    let cancelled = false;
    const refresh = () =>
      NotificationsApi.unreadCount()
        .then((n) => {
          if (!cancelled) setUnread(n);
        })
        .catch(() => {});
    refresh();
    const timer = setInterval(refresh, 60_000);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, []);

  return (
    <Link to={to} className="relative rounded-md p-2 hover:bg-slate-700" title="Alerts">
      <span aria-hidden>🔔</span>
      {unread > 0 && (
        <span className="absolute -right-0.5 -top-0.5 rounded-full bg-red-600 px-1.5 text-xs font-bold text-white">
          {unread}
        </span>
      )}
    </Link>
  );
}
