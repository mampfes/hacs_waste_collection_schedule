import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "test/browser",
  use: {
    baseURL: "http://127.0.0.1:5179",
    viewport: { width: 390, height: 844 },
  },
  webServer: {
    command: "npm exec vite -- --host 127.0.0.1 --port 5179",
    url: "http://127.0.0.1:5179",
    reuseExistingServer: !process.env.CI,
  },
});
