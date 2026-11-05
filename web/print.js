import { esc } from "./ui.js";

// Keep the usual print window, with an isolated iframe fallback when popups are blocked.
export function openPrintWindow() {
  const popup = window.open("", "_blank");
  if (popup) return popup;
  const frame = document.createElement("iframe");
  frame.title = "معاينة الطباعة";
  frame.setAttribute("aria-hidden", "true");
  frame.style.cssText = "position:fixed;left:-10000px;top:0;width:1px;height:1px;border:0";
  document.body.appendChild(frame);
  const win = frame.contentWindow;
  if (!win) { frame.remove(); return null; }
  const cleanup = () => setTimeout(() => frame.remove(), 250);
  win.addEventListener("afterprint", cleanup, { once: true });
  win.__codexPrintCleanup = cleanup;
  setTimeout(cleanup, 60000);
  return win;
}

export function openPrintDocument(title, body, orientation = "landscape") {
  const w = openPrintWindow();
  if (!w) return false;
  const safeTitle = esc(title);
  w.document.open();
  w.document.write(`<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${safeTitle}</title><style>
    @page{size:A4 ${orientation};margin:12mm}*{box-sizing:border-box}body{font:13px Tahoma,Arial,sans-serif;color:#172b43;margin:0}header{display:flex;justify-content:space-between;align-items:center;border-bottom:2px solid #1672b8;padding:0 0 10px;margin-bottom:14px}h1{font-size:20px;margin:0;color:#145b91}.date{font-size:11px;color:#555}table{width:100%;border-collapse:collapse;margin-top:12px}th,td{border:1px solid #8796a6;padding:7px;text-align:right}th{background:#eaf3fb;color:#174f7a}.num{direction:ltr;text-align:left;white-space:nowrap}.meta{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}.meta div{border:1px solid #b7c5d3;padding:8px}.note{margin-top:14px;white-space:pre-wrap}footer{margin-top:30px;display:flex;justify-content:space-around}.sign{min-width:150px;text-align:center;border-top:1px solid #555;padding-top:7px}
    @media print{thead{display:table-header-group}tr{break-inside:avoid;page-break-inside:avoid}}
  </style></head><body><header><h1>${safeTitle}</h1><span class="date">تاريخ الطباعة: ${esc(new Date().toLocaleString("ar-EG"))}</span></header>${body}</body></html>`);
  w.document.close();
  let printed = false;
  const print = () => {
    if (printed || w.closed) return;
    printed = true;
    w.focus();
    w.print();
  };
  w.addEventListener("load", () => setTimeout(print, 150), { once: true });
  // about:blank may already have fired load before the handler is attached.
  setTimeout(print, 600);
  return true;
}
