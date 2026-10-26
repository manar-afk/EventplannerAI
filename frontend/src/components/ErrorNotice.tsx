import React from "react";

interface ErrorNoticeProps {
  title?: string;
  message: string;
  onDismiss?: () => void;
  type?: "error" | "warning" | "info";
}

export const ErrorNotice: React.FC<ErrorNoticeProps> = ({
  title = "Notice",
  message,
  onDismiss,
  type = "error"
}) => {
  const colorClasses = {
    error: "bg-red-50 border-red-300 text-red-900",
    warning: "bg-amber-50 border-amber-300 text-amber-900",
    info: "bg-blue-50 border-blue-300 text-blue-900"
  }[type];

  return (
    <div className={`p-4 border rounded-xl flex items-start justify-between gap-3 shadow-sm ${colorClasses}`} role="alert">
      <div>
        <p className="font-semibold text-sm">{title}</p>
        <p className="text-sm mt-0.5 opacity-90">{message}</p>
      </div>
      {onDismiss && (
        <button
          onClick={onDismiss}
          className="text-sm font-bold opacity-60 hover:opacity-100 p-1"
          aria-label="Dismiss alert"
        >
          ✕
        </button>
      )}
    </div>
  );
};
