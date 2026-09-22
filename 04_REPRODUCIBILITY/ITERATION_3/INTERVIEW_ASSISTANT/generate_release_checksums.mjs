import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(scriptDir, "../../..");
const outputPath = path.join(scriptDir, "SHA256SUMS.txt");
const roots = [
  path.join(repoRoot, "02_RAW_SOURCE_DATA", "ITERATION_3", "INTERVIEW_ASSISTANT"),
  path.join(repoRoot, "03_PROCESSED_DATA", "ITERATION_3", "INTERVIEW_ASSISTANT"),
  scriptDir,
];

async function filesUnder(directory) {
  const results = [];
  for (const entry of await fs.readdir(directory, { withFileTypes: true })) {
    const item = path.join(directory, entry.name);
    if (entry.isDirectory()) results.push(...(await filesUnder(item)));
    else if (item !== outputPath) results.push(item);
  }
  return results;
}

const files = (await Promise.all(roots.map(filesUnder))).flat().sort();
const lines = [];
for (const file of files) {
  const digest = crypto.createHash("sha256").update(await fs.readFile(file)).digest("hex");
  lines.push(`${digest}  ${path.relative(repoRoot, file).split(path.sep).join("/")}`);
}

await fs.writeFile(outputPath, `${lines.join("\n")}\n`, "utf8");
console.log(JSON.stringify({ output: path.relative(repoRoot, outputPath), files: lines.length }, null, 2));
