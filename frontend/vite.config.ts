import { defineConfig } from "vitest/config";
export default defineConfig({
  build: {
    target: "es2022",
    outDir: "../custom_components/waste_collection_schedule/frontend",
    emptyOutDir: true,
    lib: {
      entry: "src/cards.ts",
      formats: ["es"],
      fileName: () => "waste-collection-cards.js",
    },
  },
  test: { include: ["test/*.test.ts"] },
});
