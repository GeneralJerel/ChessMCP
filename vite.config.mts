import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";
import fs from "node:fs";

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: "assets",
    emptyOutDir: true,
    rollupOptions: {
      input: {
        "chess-board": path.resolve(__dirname, "src/chess-board/index.tsx"),
      },
      output: {
        format: "es",
        entryFileNames: "[name].js",
        chunkFileNames: "[name].js",
        assetFileNames: "[name].[ext]",
      },
      plugins: [
        {
          name: "wrap-in-html",
          generateBundle(_, bundle) {
            const jsFiles: string[] = [];
            const cssFiles: string[] = [];

            for (const [fileName, file] of Object.entries(bundle)) {
              if (fileName.endsWith(".js")) {
                jsFiles.push(fileName);
              } else if (fileName.endsWith(".css")) {
                cssFiles.push(fileName);
              }
            }

            for (const jsFile of jsFiles) {
              const componentName = jsFile.replace(".js", "");
              const jsCode = (bundle[jsFile] as any).code;
              const cssFile = cssFiles.find((f) => f.startsWith(componentName));
              const cssCode = cssFile ? (bundle[cssFile] as any).source : "";

              const html = `<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
${cssCode ? `  <style>${cssCode}</style>` : ""}
</head>
<body>
  <div id="${componentName}-root"></div>
  <script type="module">
${jsCode}
  </script>
</body>
</html>`;

              this.emitFile({
                type: "asset",
                fileName: `${componentName}.html`,
                source: html,
              });

              // Remove standalone JS and CSS files
              delete bundle[jsFile];
              if (cssFile) delete bundle[cssFile];
            }
          },
        },
      ],
    },
  },
  server: {
    port: 4444,
    strictPort: true,
    cors: true,
  },
  esbuild: {
    jsx: "automatic",
    jsxImportSource: "react",
    target: "es2022",
  },
});

