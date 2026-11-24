import "./index.css";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { App } from "./App";
import { ApiError } from "./lib/api";
import { initTelegram } from "./lib/telegram";

const queryClient = new QueryClient({
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

const insideTelegram = await initTelegram();

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <App insideTelegram={insideTelegram} />
    </QueryClientProvider>
  </StrictMode>,
);
