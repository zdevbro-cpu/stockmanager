export const loadJson = <T>(key: string, fallback: T) => {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return fallback;
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
};

export const saveJson = <T>(key: string, value: T) => {
  localStorage.setItem(key, JSON.stringify(value));
};
