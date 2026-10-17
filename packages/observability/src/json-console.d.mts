// Types for json-console.mjs, which stays plain JavaScript so Node can
// preload it before Next.js starts.
export const SERVICE: string;

export function jsonLine(
    level: string,
    args: unknown[],
    service?: string,
    now?: Date,
): string;

export function useJsonConsole(service?: string): void;
