/**
 * Production-safe logger that only outputs in development mode.
 * Vite sets import.meta.env.DEV to true during development
 * and strips it in production builds via dead-code elimination.
 */
const isDev = import.meta.env.DEV;

export const logger = {
  log(...args: unknown[]): void {
    if (isDev) {
      console.log(...args);
    }
  },
  warn(...args: unknown[]): void {
    if (isDev) {
      console.warn(...args);
    }
  },
  error(...args: unknown[]): void {
    if (isDev) {
      console.error(...args);
    }
  },
};
