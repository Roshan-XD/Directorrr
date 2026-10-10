export const message = (error: unknown) =>
  error instanceof Error
    ? error.message
    : "Operation failed. Refresh before retrying.";
