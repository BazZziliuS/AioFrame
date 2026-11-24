/** TanStack Query keys in one place: invalidate a whole group by its prefix. */
export const queryKeys = {
  me: ["me"] as const,
  admin: {
    all: ["admin"] as const,
    stats: ["admin", "stats"] as const,
    users: (query: string) => ["admin", "users", query] as const,
    settings: ["admin", "settings"] as const,
  },
};
