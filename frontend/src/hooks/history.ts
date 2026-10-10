const KEY = "director.job-ids.v1";
export const jobIdPattern = /^[0-9a-f]{32}$/;
export function readHistory(): string[] {
  try {
    const value: unknown = JSON.parse(sessionStorage.getItem(KEY) ?? "[]");
    return Array.isArray(value)
      ? [
          ...new Set(
            value.filter(
              (id): id is string =>
                typeof id === "string" && jobIdPattern.test(id),
            ),
          ),
        ].slice(0, 12)
      : [];
  } catch {
    return [];
  }
}
export function writeHistory(ids: string[]) {
  try {
    sessionStorage.setItem(KEY, JSON.stringify(ids.slice(0, 12)));
  } catch {
    /* History is optional when browser storage is unavailable. */
  }
}
