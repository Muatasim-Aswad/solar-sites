import { defineConfig } from "vite-plus";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  test: { include: ["src/**/*.test.{ts,tsx}"] },
  server: {
    host: "127.0.0.1",
    port: 5173,
    strictPort: true,
    proxy: { "/api": { target: "http://127.0.0.1:8000", changeOrigin: false } },
  },
  lint: {
    plugins: ["typescript", "react", "jsx-a11y", "import"],
    options: { typeAware: true, typeCheck: true },
    ignorePatterns: ["src/infra/api/schema.d.ts", "dist/**"],
    rules: {
      "import/no-cycle": ["error", { ignoreExternal: true, ignoreTypes: false }],
      "typescript/no-deprecated": "error",
    },
    overrides: [
      {
        files: ["src/features/**"],
        rules: {
          "no-restricted-imports": [
            "error",
            {
              patterns: [{ regex: "(^|/)app(/|$)", message: "Features must not import app code." }],
            },
          ],
        },
      },
      {
        files: ["src/infra/**"],
        rules: {
          "no-restricted-imports": [
            "error",
            {
              patterns: [
                {
                  regex: "(^|/)(app|features)(/|$)",
                  message: "Infrastructure must not import app or feature code.",
                },
              ],
            },
          ],
        },
      },
      {
        files: ["src/shared/**"],
        rules: {
          "no-restricted-imports": [
            "error",
            {
              patterns: [
                {
                  regex: "(^|/)(app|features|infra|config)(/|$)",
                  message: "Shared code must not import other application layers.",
                },
              ],
            },
          ],
        },
      },
    ],
  },
  fmt: { ignorePatterns: ["src/infra/api/schema.d.ts", "pnpm-lock.yaml", "dist/**"] },
});
