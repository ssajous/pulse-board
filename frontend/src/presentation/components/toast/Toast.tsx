import { useEffect } from "react";
import { Activity, AlertCircle } from "lucide-react";

const AUTO_DISMISS_MS = 3000;

interface ToastProps {
  message: string;
  type: "success" | "error";
  onClose: () => void;
}

export function Toast({ message, type, onClose }: ToastProps) {
  useEffect(() => {
    const timer = setTimeout(onClose, AUTO_DISMISS_MS);
    return () => clearTimeout(timer);
  }, [onClose]);

  const Icon = type === "error" ? AlertCircle : Activity;
  const bgClass = type === "error" ? "bg-rose-500" : "bg-indigo-600";

  return (
    <div
      id="toast"
      className={`fixed bottom-4 right-4 z-50 flex items-center gap-2 rounded-lg ${bgClass} px-4 py-3 text-white shadow-lg animate-slide-up`}
    >
      <Icon size={18} />
      <span className="text-sm font-medium">{message}</span>
    </div>
  );
}
