import { QueryClient } from "@tanstack/react-query";

import { ApiError } from "@/api";

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      // Retry only transient failures: auth, bans and maintenance (503) will not change
      retry: (failureCount, error) => {
        if (!(error instanceof ApiError)) return failureCount < 2;
        const transient = error.status === 0 || (error.status >= 500 && error.status !== 503);
        return transient && failureCount < 2;
      },
    },
  },
});
