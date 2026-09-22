import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const [inputPath, outputDir] = process.argv.slice(2);

if (!inputPath || !outputDir) {
  throw new Error("Usage: node export_interview_workbook_csv.mjs <input.xlsx> <output-dir>");
}

const fileNames = new Map([
  ["Overview", "overview.csv"],
  ["Sources & Licences", "sources_and_licences.csv"],
  ["Data Notes", "data_notes.csv"],
  ["MASCO Roles", "masco_roles.csv"],
  ["Role Anchors", "role_anchors.csv"],
  ["Global Matches", "global_matches.csv"],
  ["Interview Q&A", "interview_qa.csv"],
  ["Open Q&A", "open_qa.csv"],
  ["Open QA Links", "open_qa_links.csv"],
  ["Rubrics", "rubrics.csv"],
  ["Coverage", "coverage.csv"],
  ["Data Quality", "data_quality.csv"],
]);

function csvCell(value) {
  if (value === null || value === undefined) return "";
  const text = value instanceof Date ? value.toISOString() : String(value);
  return /[",\r\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

const input = await FileBlob.load(inputPath);
const workbook = await SpreadsheetFile.importXlsx(input);
const sheetInspection = await workbook.inspect({
  kind: "sheet",
  include: "id,name",
  maxChars: 6000,
});
const sheetSummary = sheetInspection.ndjson
  .trim()
  .split("\n")
  .filter(Boolean)
  .map((line) => JSON.parse(line));

await fs.mkdir(outputDir, { recursive: true });

const exported = [];
for (const record of sheetSummary) {
  const sheetName = record.name;
  const fileName = fileNames.get(sheetName);
  if (!fileName) throw new Error(`No CSV filename configured for worksheet: ${sheetName}`);

  const sheet = workbook.worksheets.getItem(sheetName);
  const usedRange = sheet.getUsedRange(true);
  const rows = usedRange?.values ?? [];
  const csv = `${rows.map((row) => row.map(csvCell).join(",")).join("\r\n")}\r\n`;
  const outputPath = path.join(outputDir, fileName);
  await fs.writeFile(outputPath, csv, "utf8");
  exported.push({ sheet: sheetName, file: fileName, rows: rows.length, columns: rows[0]?.length ?? 0 });
}

const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!",
  options: { useRegex: true, maxResults: 300 },
  summary: "final formula error scan",
  maxChars: 6000,
});

console.log(JSON.stringify({ exported, formulaErrorScan: errors.ndjson }, null, 2));
