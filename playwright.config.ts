import { defineConfig } from "@playwright/test";

const port = 18000;
const baseURL = `http://127.0.0.1:${port}`;

export default defineConfig({
  testDir: "./e2e",
  workers: 1,
  forbidOnly: Boolean(process.env.CI),
  use: { browserName: "chromium", baseURL, trace: "retain-on-failure" },
  webServer: {
    command:
      "pnpm --dir apps/frontend run build && uv run --no-sync --project apps/backend python e2e/server.py",
    url: `${baseURL}/readyz`,
    env: { E2E_PORT: String(port) },
    reuseExistingServer: false,
    gracefulShutdown: { signal: "SIGINT", timeout: 10_000 },
    timeout: 120_000,
  },
});
