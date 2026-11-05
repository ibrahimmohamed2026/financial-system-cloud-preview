// عميل API: توكنات + تجديد تلقائي. التوكنات في sessionStorage (بتتمسح بقفل التبويب).
const K = "fs_auth";
const store = {
  get() { try { return JSON.parse(sessionStorage.getItem(K)); } catch { return null; } },
  set(v) { try { sessionStorage.setItem(K, JSON.stringify(v)); } catch {} },
  clear() { try { sessionStorage.removeItem(K); } catch {} },
};
export const auth = {
  get user() { return store.get()?.user || null; },
  get token() { return store.get()?.access || null; },
  get perms() { return store.get()?.perms || []; },
  can(screen, action) { return this.perms.some(p => p.screen === screen && p.action === action); },
  save(t, perms) { store.set({ access: t.access_token, refresh: t.refresh_token, user: t.user, perms: perms ?? this.perms }); },
  updateUser(fields) { const s=store.get(); if(s){s.user={...s.user,...fields};store.set(s);} },
  clear: () => store.clear(),
  get loggedIn() { return !!store.get()?.access; },
};
export class ApiError extends Error { constructor(status, detail) { super(typeof detail === "string" ? detail : "خطأ"); this.status = status; this.detail = detail; } }

let refreshing = null;
async function refresh() {
  const s = store.get(); if (!s?.refresh) return false;
  refreshing ??= fetch("/auth/refresh", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ refresh_token: s.refresh }) })
    .then(async r => { if (!r.ok) return false; auth.save(await r.json()); return true; }).catch(() => false).finally(() => (refreshing = null));
  return refreshing;
}
export async function api(path, { method = "GET", json, form, raw } = {}, retry = true) {
  const headers = {}; let body;
  const s = store.get(); if (s?.access) headers.Authorization = "Bearer " + s.access;
  if (json !== undefined) { headers["Content-Type"] = "application/json"; body = JSON.stringify(json); }
  if (form) body = form;
  const r = await fetch(path, { method, headers, body });
  if (r.status === 401 && retry && s && await refresh()) return api(path, { method, json, form, raw }, false);
  if (r.status === 401 && s) { auth.clear(); location.hash = "#/login"; }
  if (!r.ok) { let d; try { d = (await r.json()).detail; } catch { d = r.statusText; } throw new ApiError(r.status, d); }
  if (raw) return r;
  return r.status === 204 ? null : r.json();
}

const avatarUrls = new Map();
export async function userAvatarUrl(userId, version) {
  if (!userId || !version) return null;
  const key = `${userId}:${version}`;
  if (avatarUrls.has(key)) return avatarUrls.get(key);
  const response = await api(`/admin/users/${userId}/avatar`, { raw: true });
  const url = URL.createObjectURL(await response.blob());
  for (const [oldKey, oldUrl] of avatarUrls) {
    if (oldKey.startsWith(`${userId}:`)) { URL.revokeObjectURL(oldUrl); avatarUrls.delete(oldKey); }
  }
  avatarUrls.set(key, url);
  return url;
}

export async function login(username, password) {
  const t = await api("/auth/login", { method: "POST", json: { username, password } });
  auth.save(t, []);
  const me = await api("/auth/me");
  let manual = false, current = "ar";
  try { manual = localStorage.getItem("fs_lang_manual") === "1"; current = localStorage.getItem("fs_lang") === "en" ? "en" : "ar"; } catch {}
  const preferred = manual ? current : (me.preferred_language === "en" ? "en" : "ar");
  try { localStorage.setItem("fs_lang", preferred); localStorage.removeItem("fs_lang_manual"); } catch {}
  auth.save({ ...t, user: { ...t.user, ...me, preferred_language: preferred } }, me.permissions);
  if (manual && preferred !== me.preferred_language) {
    try { await api("/auth/language", { method: "PUT", json: { language: preferred } }); } catch {}
  }
}

export async function downloadFile(path, name, open) {
  const r = await api(path, { raw: true }); const url = URL.createObjectURL(await r.blob());
  if (open) window.open(url, "_blank"); else { const a = document.createElement("a"); a.href = url; a.download = name; a.click(); }
  setTimeout(() => URL.revokeObjectURL(url), 60000);
}
