// ADEX ERP language foundation. UI language is independent from business data.
const STORAGE_KEY = "fs_lang";
export const getLanguage = () => {
  try { return localStorage.getItem(STORAGE_KEY) === "en" ? "en" : "ar"; }
  catch { return "ar"; }
};
export const isEnglish = () => getLanguage() === "en";
export const translate = (arabic, english) => isEnglish() ? english : arabic;
export const setLanguage = language => {
  const next = language === "en" ? "en" : "ar";
  try { localStorage.setItem(STORAGE_KEY, next); } catch {}
  applyLanguage(next);
  return next;
};
export const applyLanguage = (language = getLanguage()) => {
  const en = language === "en";
  document.documentElement.lang = en ? "en" : "ar";
  document.documentElement.dir = en ? "ltr" : "rtl";
  document.documentElement.dataset.language = language;
};
