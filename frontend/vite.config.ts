import { defineConfig } from "vitest/config";
import { readFileSync } from "node:fs";
export default defineConfig({
  plugins: [
    {
      name: "third-party-notices",
      generateBundle() {
        const packages = [
          "lit",
          "lit-html",
          "lit-element",
          "@lit/reactive-element",
        ];
        const notices = packages.map((name) => {
          const root = new URL(`./node_modules/${name}/`, import.meta.url);
          const { version } = JSON.parse(
            readFileSync(new URL("package.json", root), "utf8"),
          );
          return `${name} ${version}\n${readFileSync(new URL("LICENSE", root), "utf8")}`;
        });
        this.emitFile({
          type: "asset",
          fileName: "THIRD-PARTY-NOTICES.txt",
          source: `Third-party software included in waste-collection-cards.js\n\n${notices.join("\n\n")}\n`,
        });
      },
    },
  ],
  build: {
    target: "es2022",
    outDir: "../custom_components/waste_collection_schedule/frontend",
    emptyOutDir: true,
    rollupOptions: {
      output: {
        banner:
          "/* Generated from frontend/src by `npm run build`. Do not edit by hand. */",
      },
    },
    lib: {
      entry: "src/cards.ts",
      formats: ["es"],
      fileName: () => "waste-collection-cards.js",
    },
  },
  test: { include: ["test/*.test.ts"] },
});
