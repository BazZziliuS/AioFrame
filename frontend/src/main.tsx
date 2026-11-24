import "@/styles/index.css";

import { createRoot } from "react-dom/client";

import { App } from "@/app/App";
import { AppProviders } from "@/app/providers";
import { initTelegram } from "@/shared/telegram/sdk";

const insideTelegram = await initTelegram();

createRoot(document.getElementById("root")!).render(
  <AppProviders>
    <App insideTelegram={insideTelegram} />
  </AppProviders>,
);
