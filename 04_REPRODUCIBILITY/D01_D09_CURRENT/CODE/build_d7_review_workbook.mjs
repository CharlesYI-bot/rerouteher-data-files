import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { SpreadsheetFile, Workbook } from "/Users/charlesyi/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(scriptDir, "..");
const sourceDir = path.join(root, "03_EMPLOYER_EVIDENCE");
const threadId = "01a04198-62bd-7390-96c9-e1956ffe7543";
const outputDir = path.join(root, "outputs", threadId);
const qaDir = path.join(root, "06_QA", "workbook_render");

await fs.mkdir(outputDir, { recursive: true });
await fs.mkdir(qaDir, { recursive: true });

const workbook = Workbook.create();
const summary = workbook.worksheets.add("Summary");

function parseCsv(csvText) {
  const rows = [];
  let row = [];
  let field = "";
  let quoted = false;
  for (let index = 0; index < csvText.length; index += 1) {
    const char = csvText[index];
    if (quoted) {
      if (char === '"' && csvText[index + 1] === '"') {
        field += '"';
        index += 1;
      } else if (char === '"') {
        quoted = false;
      } else {
        field += char;
      }
    } else if (char === '"') {
      quoted = true;
    } else if (char === ",") {
      row.push(field);
      field = "";
    } else if (char === "\n") {
      row.push(field.endsWith("\r") ? field.slice(0, -1) : field);
      rows.push(row);
      row = [];
      field = "";
    } else {
      field += char;
    }
  }
  if (field.length > 0 || row.length > 0) {
    row.push(field);
    rows.push(row);
  }
  const width = rows[0].length;
  const headers = rows[0];
  return rows.filter((values) => values.some((value) => value !== "")).map((values, rowIndex) => {
    const padded = [...values, ...Array(Math.max(0, width - values.length)).fill("")].slice(0, width);
    if (rowIndex === 0) return padded;
    return padded.map((value, columnIndex) => {
      if (value === "") return null;
      if (["employer_id", "evidence_id"].includes(headers[columnIndex])) return value;
      if (value === "True") return true;
      if (value === "False") return false;
      if (/^-?(?:\d+|\d*\.\d+)$/.test(value)) return Number(value);
      return value;
    });
  });
}

for (const [filename, sheetName] of [
  ["D7_employer_universe_50.csv", "Employers"],
  ["D7_evidence_lineage.csv", "Evidence"],
  ["D7_report_search_audit_50.csv", "Search Audit"],
  ["D7_manual_validation_queue_50.csv", "Review Queue"],
  ["D7_scoring_rules.csv", "Scoring Rules"],
]) {
  const csvText = await fs.readFile(path.join(sourceDir, filename), "utf8");
  const values = parseCsv(csvText);
  const sheet = workbook.worksheets.add(sheetName);
  sheet.getRangeByIndexes(0, 0, values.length, values[0].length).values = values;
}

const navy = "#17324D";
const teal = "#0F766E";
const paleTeal = "#DDF3F0";
const paleBlue = "#EAF2F8";
const gold = "#D69E2E";
const paleGold = "#FFF4CE";
const red = "#B42318";
const paleRed = "#FDECEC";
const green = "#137333";
const paleGreen = "#E6F4EA";
const grid = "#D7DEE5";
const muted = "#526575";

function titleBlock(sheet, title, subtitle, endColumn) {
  sheet.getRange(`A1:${endColumn}1`).merge();
  sheet.getRange("A1").values = [[title]];
  sheet.getRange(`A1:${endColumn}1`).format = {
    fill: navy,
    font: { bold: true, color: "#FFFFFF", size: 16 },
    verticalAlignment: "center",
  };
  sheet.getRange(`A1:${endColumn}1`).format.rowHeight = 28;
  sheet.getRange(`A2:${endColumn}2`).merge();
  sheet.getRange("A2").values = [[subtitle]];
  sheet.getRange(`A2:${endColumn}2`).format = {
    fill: paleBlue,
    font: { color: muted, italic: true },
    wrapText: true,
  };
  sheet.getRange(`A2:${endColumn}2`).format.rowHeight = 34;
  sheet.showGridLines = false;
}

function styleImportedSheet(sheet, usedAddress, headerAddress) {
  sheet.showGridLines = false;
  sheet.freezePanes.freezeRows(1);
  sheet.getRange(usedAddress).format = {
    font: { color: "#1F2933", size: 10 },
    verticalAlignment: "top",
    borders: { preset: "all", style: "thin", color: grid },
  };
  sheet.getRange(headerAddress).format = {
    fill: teal,
    font: { bold: true, color: "#FFFFFF" },
    wrapText: true,
    verticalAlignment: "center",
  };
  sheet.getRange(headerAddress).format.rowHeight = 36;
}

titleBlock(
  summary,
  "ReRouteHer D7 Employer Evidence Review",
  "Live review controls for the 50-company candidate universe. After the completed official-source search, an unsupported pillar is scored 0; raw undisclosed facts remain blank.",
  "H",
);
summary.getRange("A4:B4").merge();
summary.getRange("C4:E4").merge();
summary.getRange("A4").values = [["Control"]];
summary.getRange("C4").values = [["Live value"]];
for (let row = 5; row <= 8; row += 1) {
  summary.getRange(`A${row}:B${row}`).merge();
  summary.getRange(`C${row}:E${row}`).merge();
}
summary.getRange("A9:B9").merge();
summary.getRange("C9:H9").merge();
summary.getRange("A5:A9").values = [
  ["Candidate employers"],
  ["Reports located and reviewed"],
  ["Atomic evidence rows"],
  ["Completed review decisions"],
  ["Production score status"],
];
summary.getRange("C5").formulas = [["=COUNTA('Employers'!A2:A51)"]];
summary.getRange("C6").formulas = [["=COUNTIF('Search Audit'!C2:C51,\"report_located_and_reviewed\")"]];
summary.getRange("C7").formulas = [["=COUNTA('Evidence'!A2:A200)"]];
summary.getRange("C8").formulas = [["=COUNTIF('Review Queue'!H2:H51,\"approved\")+COUNTIF('Review Queue'!H2:H51,\"approved_with_edits\")"]];
summary.getRange("C9").formulas = [["=IF(AND(C8=50,COUNT('Employers'!K2:K51)=50),\"APPROVED evidence; 50 scores use the completed-search zero-fill policy\",\"BLOCKED until evidence, score and second-review gates close\")"]];
summary.getRange("A4:B4").format = { fill: teal, font: { bold: true, color: "#FFFFFF" } };
summary.getRange("C4:E4").format = { fill: teal, font: { bold: true, color: "#FFFFFF" } };
summary.getRange("A5:B9").format = { fill: paleTeal, font: { bold: true, color: navy } };
summary.getRange("A4:E9").format.borders = { preset: "all", style: "thin", color: grid };
summary.getRange("A11:H11").merge();
summary.getRange("A11").values = [["Reviewer workflow"]];
summary.getRange("A11:H11").format = { fill: navy, font: { bold: true, color: "#FFFFFF" } };
summary.getRange("A12:H16").values = [
  ["1", "Search", "Complete the two-stage sustainability/annual-report search in Search Audit.", "", "", "", "", ""],
  ["2", "Extract", "Record one normalized fact per Evidence row with URL, year and page/section locator.", "", "", "", "", ""],
  ["3", "Score", "Enter confirmed 0–100 pillar scores in Employers columns H:J; after the completed search, score an unsupported pillar as 0.", "", "", "", "", ""],
  ["4", "Review", "A second reviewer checks source, fact, normalization and deterministic scoring.", "", "", "", "", ""],
  ["5", "Approve", "Record reviewer, date and decision in Review Queue. Raw undisclosed facts remain blank even when the scoring pillar is zero-filled.", "", "", "", "", ""],
];
summary.getRange("A12:A16").format = { fill: gold, font: { bold: true, color: "#FFFFFF" }, horizontalAlignment: "center" };
summary.getRange("B12:B16").format = { fill: paleGold, font: { bold: true, color: navy } };
summary.getRange("C12:H16").merge(true);
summary.getRange("A12:H16").format = { wrapText: true, verticalAlignment: "center", borders: { preset: "all", style: "thin", color: grid } };
summary.getRange("A12:H16").format.rowHeight = 30;
summary.getRange("A:A").format.columnWidth = 12;
summary.getRange("B:B").format.columnWidth = 30;
summary.getRange("C:H").format.columnWidth = 15;
summary.freezePanes.freezeRows(2);

const employers = workbook.worksheets.getItem("Employers");
styleImportedSheet(employers, "A1:Q51", "A1:Q1");
employers.getRange("A2:A51").format.numberFormat = "@";
employers.getRange("P1:Q1").values = [["formula_official_score", "evidence_confidence"]];
employers.getRange("P1:Q1").format = { fill: navy, font: { bold: true, color: "#FFFFFF" }, wrapText: true };
employers.getRange("P2").formulas = [["=IF(COUNT(H2:J2)=3,ROUND(0.3*H2+0.4*I2+0.3*J2,1),\"\")"]];
employers.getRange("P2:P51").fillDown();
employers.getRange("Q2").formulas = [["=L2"]];
employers.getRange("Q2:Q51").fillDown();
employers.getRange("H2:J51").format.numberFormat = "0.0";
employers.getRange("K2:K51").format.numberFormat = "0.0";
employers.getRange("P2:P51").format.numberFormat = "0.0";
employers.dataValidations.add({ range: "H2:J51", rule: { type: "decimal", operator: "between", formula1: 0, formula2: 100 } });
employers.getRange("M2:M51").conditionalFormats.add("containsText", { text: "blocked", format: { fill: paleRed, font: { color: red, bold: true } } });
employers.getRange("M2:M51").conditionalFormats.add("containsText", { text: "approved", format: { fill: paleGreen, font: { color: green, bold: true } } });
employers.getRange("N2:N51").conditionalFormats.add("containsText", { text: "pending", format: { fill: paleGold, font: { color: "#7A4E00" } } });
employers.getRange("N2:N51").conditionalFormats.add("containsText", { text: "approved", format: { fill: paleGreen, font: { color: green, bold: true } } });
employers.getRange("A:A").format.columnWidth = 10;
employers.getRange("B:B").format.columnWidth = 28;
employers.getRange("C:C").format.columnWidth = 10;
employers.getRange("D:D").format.columnWidth = 22;
employers.getRange("E:F").format.columnWidth = 12;
employers.getRange("G:G").format.columnWidth = 36;
employers.getRange("H:K").format.columnWidth = 14;
employers.getRange("L:N").format.columnWidth = 24;
employers.getRange("O:O").format.columnWidth = 42;
employers.getRange("P:Q").format.columnWidth = 18;
employers.getRange("B2:Q51").format.wrapText = true;

const evidence = workbook.worksheets.getItem("Evidence");
styleImportedSheet(evidence, "A1:N200", "A1:N1");
evidence.getRange("A2:B200").format.numberFormat = "@";
evidence.getRange("L2:L200").dataValidation = { rule: { type: "list", values: ["source_confirmed_pending_second_reviewer", "verified", "needs_correction", "rejected"] } };
evidence.getRange("L2:L200").conditionalFormats.add("containsText", { text: "pending", format: { fill: paleGold, font: { color: "#7A4E00" } } });
evidence.getRange("L2:L200").conditionalFormats.add("containsText", { text: "verified", format: { fill: paleGreen, font: { color: green, bold: true } } });
evidence.getRange("A:A").format.columnWidth = 12;
evidence.getRange("B:B").format.columnWidth = 10;
evidence.getRange("C:C").format.columnWidth = 26;
evidence.getRange("D:E").format.columnWidth = 22;
evidence.getRange("F:H").format.columnWidth = 12;
evidence.getRange("I:I").format.columnWidth = 38;
evidence.getRange("J:J").format.columnWidth = 16;
evidence.getRange("K:K").format.columnWidth = 48;
evidence.getRange("L:N").format.columnWidth = 24;
evidence.getRange("C2:N200").format.wrapText = true;

const search = workbook.worksheets.getItem("Search Audit");
styleImportedSheet(search, "A1:I51", "A1:I1");
search.getRange("A2:A51").format.numberFormat = "@";
search.getRange("C2:C51").dataValidation = { rule: { type: "list", values: ["not_completed", "report_located_and_reviewed", "completed_no_report_found"] } };
search.getRange("C2:C51").conditionalFormats.add("containsText", { text: "not_completed", format: { fill: paleRed, font: { color: red, bold: true } } });
search.getRange("C2:C51").conditionalFormats.add("containsText", { text: "reviewed", format: { fill: paleGreen, font: { color: green } } });
search.getRange("A:A").format.columnWidth = 10;
search.getRange("B:B").format.columnWidth = 28;
search.getRange("C:C").format.columnWidth = 26;
search.getRange("D:E").format.columnWidth = 12;
search.getRange("F:F").format.columnWidth = 42;
search.getRange("G:H").format.columnWidth = 24;
search.getRange("I:I").format.columnWidth = 48;
search.getRange("B2:I51").format.wrapText = true;

const review = workbook.worksheets.getItem("Review Queue");
styleImportedSheet(review, "A1:I51", "A1:I1");
review.getRange("A2:A51").format.numberFormat = "@";
review.getRange("D2:D51").dataValidation = { rule: { type: "list", values: ["report_search_pending", "evidence_second_review_pending", "in_review", "complete", "rejected"] } };
review.getRange("H2:H51").dataValidation = { rule: { type: "list", values: ["approved", "approved_with_edits", "needs_correction", "rejected"] } };
review.getRange("C2:C51").conditionalFormats.add("containsText", { text: "high", format: { fill: paleRed, font: { color: red, bold: true } } });
review.getRange("D2:D51").conditionalFormats.add("containsText", { text: "pending", format: { fill: paleGold, font: { color: "#7A4E00" } } });
review.getRange("H2:H51").conditionalFormats.add("containsText", { text: "approved", format: { fill: paleGreen, font: { color: green, bold: true } } });
review.getRange("A:A").format.columnWidth = 10;
review.getRange("B:B").format.columnWidth = 28;
review.getRange("C:D").format.columnWidth = 20;
review.getRange("E:E").format.columnWidth = 52;
review.getRange("F:H").format.columnWidth = 20;
review.getRange("I:I").format.columnWidth = 42;
review.getRange("B2:I51").format.wrapText = true;

const rules = workbook.worksheets.getItem("Scoring Rules");
styleImportedSheet(rules, "A1:D20", "A1:D1");
rules.getRange("A:A").format.columnWidth = 22;
rules.getRange("B:B").format.columnWidth = 34;
rules.getRange("C:C").format.columnWidth = 18;
rules.getRange("D:D").format.columnWidth = 72;
rules.getRange("A2:D20").format.wrapText = true;
rules.getRange("D2:D20").conditionalFormats.add("containsText", { text: "unsupported pillar", format: { fill: paleGold, font: { color: "#7A4E00", bold: true } } });

const keyInspection = await workbook.inspect({
  kind: "table",
  range: "Summary!A1:H16",
  include: "values,formulas",
  tableMaxRows: 20,
  tableMaxCols: 10,
});
await fs.writeFile(path.join(qaDir, "key_range_inspection.ndjson"), keyInspection.ndjson, "utf8");
const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 300 },
  summary: "final formula error scan",
});
await fs.writeFile(path.join(qaDir, "formula_error_scan.ndjson"), errors.ndjson, "utf8");

for (const [sheetName, range] of [
  ["Summary", "A1:H16"],
  ["Employers", "A1:Q18"],
  ["Evidence", "A1:N15"],
  ["Search Audit", "A1:I18"],
  ["Review Queue", "A1:I18"],
  ["Scoring Rules", "A1:D20"],
]) {
  const preview = await workbook.render({ sheetName, range, scale: 1, format: "png" });
  const safeName = sheetName.toLowerCase().replaceAll(" ", "_");
  await fs.writeFile(path.join(qaDir, `${safeName}.png`), new Uint8Array(await preview.arrayBuffer()));
}

const output = await SpreadsheetFile.exportXlsx(workbook);
const outputPath = path.join(outputDir, "ReRouteHer_D7_Evidence_Review.xlsx");
await output.save(outputPath);
console.log(JSON.stringify({ outputPath, qaDir, sheets: 6 }, null, 2));
