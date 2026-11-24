import { Toast } from "@heroui/react";
import { QueryClientProvider } from "@tanstack/react-query";
import { StrictMode, type ReactNode } from "react";

import { queryClient } from "./queryClient";

/** Global providers: data fetching and toasts (i18n depends on the user and lives in App). */
export function AppProviders({ children }: { children: ReactNode }) {
  return (
    <StrictMode>
      <QueryClientProvider client={queryClient}>
        <Toast.Provider placement="top" />
        {children}
      </QueryClientProvider>
    </StrictMode>
  );
}
