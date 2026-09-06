"use client";

import { useState } from "react";

export function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  return (
    <button
      type="button"
      onClick={async () => {
        try {
          await navigator.clipboard.writeText(text);
          setCopied(true);
          setTimeout(() => setCopied(false), 1500);
        } catch {
          // Clipboard access can be denied by the browser; fail silently, the text is still visible to select/copy manually.
        }
      }}
      className="shrink-0 rounded-full border border-violet-200 px-2.5 py-0.5 text-xs font-medium text-violet-700 hover:bg-violet-50"
    >
      {copied ? "복사됨" : "복사"}
    </button>
  );
}
