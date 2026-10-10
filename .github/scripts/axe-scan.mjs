// Runs axe-core on every HTML page in a directory and writes one JSON file per
// page plus summary.json. Exits 0 regardless of violations: results feed the
// comparison table, they do not gate merges.
//
// With --expect=<rule,rule>, exits 1 unless every page reports every listed
// rule. CI uses this on a known-bad fixture to prove the scanner itself works.
//
// Usage: node axe-scan.mjs <pages-dir> <out-dir> [--expect=image-alt,button-name]

import { createServer } from "node:http";
import { mkdirSync, readFileSync, readdirSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { extname, join, resolve } from "node:path";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");
const axeSource = readFileSync(require.resolve("axe-core/axe.min.js"), "utf8");

const args = process.argv.slice(2);
const expect = (args.find((a) => a.startsWith("--expect="))?.slice(9) ?? "").split(",").filter(Boolean);
const [pagesDir, outDir] = args.filter((a) => !a.startsWith("--")).map((p) => resolve(p));
const types = { ".html": "text/html", ".css": "text/css", ".js": "text/javascript", ".svg": "image/svg+xml" };

const server = createServer((req, res) => {
  const path = join(pagesDir, decodeURIComponent(new URL(req.url, "http://x").pathname));
  let body;
  try {
    body = readFileSync(path);
  } catch {
    res.writeHead(404).end();
    return;
  }
  res.writeHead(200, { "content-type": types[extname(path)] ?? "application/octet-stream" });
  res.end(body);
}).listen(0);
const port = server.address().port;

mkdirSync(outDir, { recursive: true });
const browser = await chromium.launch();
const summary = {};

for (const file of readdirSync(pagesDir).filter((f) => f.endsWith(".html")).sort()) {
  const page = await browser.newPage();
  await page.goto(`http://127.0.0.1:${port}/${file}`);
  await page.addScriptTag({ content: axeSource });
  const result = await page.evaluate(() => window.axe.run());
  writeFileSync(join(outDir, file.replace(/\.html$/, ".json")), JSON.stringify(result, null, 2));
  summary[file] = result.violations.map((v) => ({ id: v.id, impact: v.impact, nodes: v.nodes.length }));
  console.log(`${file}: ${result.violations.length} violation(s) ${result.violations.map((v) => v.id).join(", ")}`);
  await page.close();
}

writeFileSync(join(outDir, "summary.json"), JSON.stringify(summary, null, 2));
await browser.close();
server.close();

const pages = Object.keys(summary);
const missing = pages.flatMap((file) =>
  expect.filter((id) => !summary[file].some((v) => v.id === id)).map((id) => `${file}: ${id}`),
);
if (expect.length && (pages.length === 0 || missing.length)) {
  console.error(`Expected violations not reported: ${pages.length ? missing.join("; ") : "no pages scanned"}`);
  process.exit(1);
}
