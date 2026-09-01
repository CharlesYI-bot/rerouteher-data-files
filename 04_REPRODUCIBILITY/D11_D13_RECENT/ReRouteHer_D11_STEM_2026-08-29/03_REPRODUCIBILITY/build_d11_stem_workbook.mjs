import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const releaseDir = path.resolve("ReRouteHer_D11_STEM_2026-08-29");
const tableDir = path.join(releaseDir, "01_TABLES");
const qaDir = path.join(releaseDir, "02_QA");
const previewDir = path.join(qaDir, "workbook_previews");
const outputDir = path.resolve("outputs/01a047e7-ceba-7df3-8d1a-ba8071e66430");
const outputPath = path.join(outputDir, "D11_STEM_D1_Structure.xlsx");

const TEAL = "#0F766E";
const NAVY = "#153B50";
const LIGHT_TEAL = "#E6F4F1";
const LIGHT_BLUE = "#E8F1F7";
const LIGHT_GRAY = "#F3F4F6";
const DARK = "#1F2937";
const MUTED = "#52606D";
const WHITE = "#FFFFFF";
const BORDER = "#D6DEE3";

const specs = [
  {
    file: "D11_STEM_roles.csv",
    sheet: "Roles",
    rows: 658,
    cols: 47,
    table: "D11StemRoles",
    preview: "A1:Q14",
    widths: { A: 16, B: 32, C: 13, D: 32, F: 15, H: 54, I: 54, P: 52, X: 18, Y: 14, AG: 34, AM: 23, AN: 40, AP: 45, AT: 20, AU: 48 },
    wrap: ["B", "D", "H", "I", "P", "AG", "AN", "AU"],
    dateColumns: ["AQ"],
  },
  {
    file: "D11_STEM_role_tasks.csv",
    sheet: "Role Tasks",
    rows: 5519,
    cols: 10,
    table: "D11StemRoleTasks",
    preview: "A1:J16",
    widths: { A: 16, B: 10, C: 22, D: 13, E: 72, F: 22, G: 48, H: 18, I: 50, J: 24 },
    wrap: ["E", "G"],
    dateColumns: ["J"],
  },
  {
    file: "D11_STEM_task_rating_lineage.csv",
    sheet: "Task Ratings",
    rows: 5519,
    cols: 16,
    table: "D11StemTaskRatings",
    preview: "A1:P16",
    widths: { A: 16, B: 22, C: 68, D: 22, E: 42, F: 22, G: 42, H: 44, N: 34, O: 22, P: 50 },
    wrap: ["C", "E", "G", "H", "N"],
  },
  {
    file: "D11_STEM_role_rating_lineage.csv",
    sheet: "Role Ratings",
    rows: 658,
    cols: 17,
    table: "D11StemRoleRatings",
    preview: "A1:Q16",
    widths: { A: 16, B: 34, C: 13, M: 24, N: 26, O: 28, P: 22, Q: 50 },
    wrap: ["B", "N", "O"],
  },
  {
    file: "D11_STEM_D1_scope_lineage.csv",
    sheet: "D1 Scope",
    rows: 11,
    cols: 6,
    table: "D11D1Scope",
    preview: "A1:F11",
    widths: { A: 14, B: 28, C: 24, D: 25, E: 50, F: 70 },
    wrap: ["B", "E", "F"],
  },
  {
    file: "D11_STEM_source_manifest.csv",
    sheet: "Sources",
    rows: 4,
    cols: 6,
    table: "D11Sources",
    preview: "A1:F4",
    widths: { A: 38, B: 70, C: 70, D: 42, E: 24, F: 52 },
    wrap: ["A", "B", "C", "D", "F"],
    dateColumns: ["E"],
  },
  {
    file: "../02_QA/D11_STEM_validation_checks.csv",
    sheet: "QA Checks",
    rows: 7,
    cols: 4,
    table: "D11QAChecks",
    preview: "A1:D7",
    widths: { A: 38, B: 78, C: 78, D: 12 },
    wrap: ["A", "B", "C"],
  },
];

function columnLabel(index) {
  let n = index;
  let result = "";
  while (n > 0) {
    n -= 1;
    result = String.fromCharCode(65 + (n % 26)) + result;
    n = Math.floor(n / 26);
  }
  return result;
}

function parseCSV(text) {
  const rows = [];
  let row = [];
  let field = "";
  let quoted = false;
  for (let i = 0; i < text.length; i += 1) {
    const char = text[i];
    if (quoted) {
      if (char === '"') {
        if (text[i + 1] === '"') {
          field += '"';
          i += 1;
        } else {
          quoted = false;
        }
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
    row.push(field.endsWith("\r") ? field.slice(0, -1) : field);
    rows.push(row);
  }
  return rows;
}

function styleDataSheet(sheet, spec) {
  const lastCol = columnLabel(spec.cols);
  const used = sheet.getRange(`A1:${lastCol}${spec.rows}`);
  const header = sheet.getRange(`A1:${lastCol}1`);
  sheet.showGridLines = false;
  sheet.freezePanes.freezeRows(1);
  used.format = {
    font: { name: "Aptos", size: 9, color: DARK },
    verticalAlignment: "top",
  };
  header.format = {
    fill: TEAL,
    font: { name: "Aptos Display", size: 10, bold: true, color: WHITE },
    wrapText: true,
    verticalAlignment: "center",
    borders: { preset: "all", style: "thin", color: "#0A5C54" },
    rowHeight: 34,
  };
  for (const [column, width] of Object.entries(spec.widths)) {
    sheet.getRange(`${column}1:${column}${spec.rows}`).format.columnWidth = width;
  }
  for (const column of spec.wrap) {
    sheet.getRange(`${column}2:${column}${spec.rows}`).format.wrapText = true;
  }
  for (const column of spec.dateColumns ?? []) {
    sheet.getRange(`${column}2:${column}${spec.rows}`).setNumberFormat("yyyy-mm-dd hh:mm");
  }
  const table = sheet.tables.add(`A1:${lastCol}${spec.rows}`, true, spec.table);
  table.style = "TableStyleMedium2";
  table.showBandedColumns = false;
  table.showFilterButton = true;
}

await fs.mkdir(outputDir, { recursive: true });
await fs.mkdir(previewDir, { recursive: true });

const workbook = Workbook.create();
const summary = workbook.worksheets.add("Summary");

for (const spec of specs) {
  const csvPath = path.resolve(tableDir, spec.file);
  const csvText = await fs.readFile(csvPath, "utf8");
  const rows = parseCSV(csvText);
  if (rows.length !== spec.rows || rows.some((row) => row.length !== spec.cols)) {
    throw new Error(`CSV shape mismatch for ${spec.file}: ${rows.length} rows`);
  }
  const normalizedRows = rows.map((row, rowIndex) =>
    row.map((value) => (rowIndex > 0 && value === "" ? null : value)),
  );
  const sheet = workbook.worksheets.add(spec.sheet);
  sheet.getRangeByIndexes(0, 0, spec.rows, spec.cols).values = normalizedRows;
}

for (const spec of specs) {
  styleDataSheet(workbook.worksheets.getItem(spec.sheet), spec);
}

summary.showGridLines = false;
summary.freezePanes.freezeRows(3);
summary.getRange("A1:H26").format.font = { name: "Aptos", color: DARK };
summary.getRange("A1:H2").merge();
summary.getRange("A1").values = [["D11 — eMASCO STEM Roles in D1 Structure"]];
summary.getRange("A1:H2").format = {
  fill: NAVY,
  font: { name: "Aptos Display", size: 20, bold: true, color: WHITE },
  horizontalAlignment: "left",
  verticalAlignment: "center",
};
summary.getRange("A3:H3").merge();
summary.getRange("A3").values = [["Official eMASCO STEM scope • six-digit MASCO role keys • D1 column contract retained • ESCO kept for comparison"]];
summary.getRange("A3:H3").format = {
  fill: TEAL,
  font: { name: "Aptos", size: 11, italic: true, color: WHITE },
  verticalAlignment: "center",
  rowHeight: 26,
};

summary.getRange("A5:B5").values = [["Validated metric", "Value"]];
summary.getRange("A6:A11").values = [
  ["Official STEM roles"],
  ["Official tasks"],
  ["Exact occupation task pages"],
  ["Official unit-group task fallbacks"],
  ["Roles with retained ESCO comparison"],
  ["Roles linked to original D1 unit groups"],
];
summary.getRange("B6:B11").formulas = [
  ["=COUNTA(Roles!$A$2:$A$658)"],
  ["=COUNTA('Role Tasks'!$A$2:$A$5519)"],
  ["=COUNTIF(Roles!$AT$2:$AT$658,\"exact_occupation\")"],
  ["=COUNTIF(Roles!$AT$2:$AT$658,\"unit_group_inherited\")"],
  ["=COUNTA(Roles!$F$2:$F$658)"],
  ["=COUNTA(Roles!$AJ$2:$AJ$658)"],
];
summary.getRange("A5:B5").format = {
  fill: TEAL,
  font: { bold: true, color: WHITE },
  borders: { preset: "all", style: "thin", color: "#0A5C54" },
};
summary.getRange("A6:B11").format = {
  fill: LIGHT_TEAL,
  font: { color: DARK },
  borders: { preset: "all", style: "thin", color: BORDER },
};
summary.getRange("B6:B11").format = {
  fill: "#D8EEE8",
  font: { bold: true, size: 12, color: NAVY },
  horizontalAlignment: "center",
  numberFormat: "0",
  borders: { preset: "all", style: "thin", color: BORDER },
};

summary.getRange("D5:H5").merge();
summary.getRange("D5").values = [["Scope and interpretation"]];
summary.getRange("D5:H5").format = { fill: TEAL, font: { bold: true, color: WHITE } };
summary.getRange("D6:H7").merge();
summary.getRange("D6").values = [["D11 is an expansion of D1 from ten seed roles to every occupation listed by eMASCO under STEM. MASCO role identifiers are stored as six digits (for example 251201) and also in official display form (2512-01)."]];
summary.getRange("D8:H9").merge();
summary.getRange("D8").values = [["The first 24 columns on Roles exactly preserve the D1 schema. ESCO fields remain comparison metadata and are populated only where the project crosswalk contains an exact six-digit mapping."]];
summary.getRange("D10:H11").merge();
summary.getRange("D10").values = [["Remote/flexible and AI labels are transparent D1-method pre-ratings. They are research-only until two independent human raters reconcile the task labels."]];
for (const address of ["D6:H7", "D8:H9", "D10:H11"]) {
  summary.getRange(address).format = {
    fill: LIGHT_BLUE,
    font: { color: DARK },
    wrapText: true,
    verticalAlignment: "center",
    borders: { preset: "outside", style: "thin", color: BORDER },
  };
}

summary.getRange("A14:B14").values = [["MASCO major group", "STEM roles"]];
summary.getRange("A15:A20").values = [["1"], ["2"], ["3"], ["4"], ["5"], ["8"]];
summary.getRange("B15:B20").formulas = [
  ["=COUNTIF(Roles!$Z$2:$Z$658,A15)"],
  ["=COUNTIF(Roles!$Z$2:$Z$658,A16)"],
  ["=COUNTIF(Roles!$Z$2:$Z$658,A17)"],
  ["=COUNTIF(Roles!$Z$2:$Z$658,A18)"],
  ["=COUNTIF(Roles!$Z$2:$Z$658,A19)"],
  ["=COUNTIF(Roles!$Z$2:$Z$658,A20)"],
];
summary.getRange("A14:B14").format = { fill: NAVY, font: { bold: true, color: WHITE } };
summary.getRange("A15:B20").format = {
  fill: LIGHT_GRAY,
  borders: { preset: "all", style: "thin", color: BORDER },
};
summary.getRange("B15:B20").format = { font: { bold: true, color: NAVY }, horizontalAlignment: "center", numberFormat: "0" };

summary.getRange("D14:H14").merge();
summary.getRange("D14").values = [["Important handoff for D12"]];
summary.getRange("D14:H14").format = { fill: "#9A3412", font: { bold: true, color: WHITE } };
summary.getRange("D15:H18").merge();
summary.getRange("D15").values = [["The existing D12 model was built against the earlier, narrower interpretation and should not be treated as the final STEM role matcher. D12 needs a new labeling/training pass whose target space is aligned to these 657 six-digit MASCO roles; JobHop v2 2019+ remains the only authorized resume dataset for that work."]];
summary.getRange("D15:H18").format = {
  fill: "#FFF1E8",
  font: { color: "#7C2D12" },
  wrapText: true,
  verticalAlignment: "center",
  borders: { preset: "outside", style: "medium", color: "#C2410C" },
};

summary.getRange("A23:H23").merge();
summary.getRange("A23").values = [["Sources and release notes"]];
summary.getRange("A23:H23").format = { fill: TEAL, font: { bold: true, color: WHITE } };
summary.getRange("A24:H24").merge();
summary.getRange("A24").values = [["Official scope: https://emasco.mohr.gov.my/directory/category/stem — definition: Occupation that includes Science, Technology, Engineering or Mathematics element."]];
summary.getRange("A25:H25").merge();
summary.getRange("A25").values = [["Portal content basis: MASCO 2020. Retrieval snapshot and page hashes are stored in the release folder. Four task lists are transparently inherited from official four-digit unit-group pages."]];
summary.getRange("A26:H26").merge();
summary.getRange("A26").values = [["No resume dataset is used in D11. ESCO mappings shown are retained comparison fields from the existing project crosswalk and remain pending domain-owner review."]];
summary.getRange("A24:H26").format = {
  fill: LIGHT_GRAY,
  font: { size: 10, color: MUTED },
  wrapText: true,
  verticalAlignment: "center",
  borders: { preset: "all", style: "thin", color: BORDER },
};

summary.getRange("A1:H2").format.font = { name: "Aptos Display", size: 20, bold: true, color: WHITE };
summary.getRange("A3:H3").format.font = { name: "Aptos", size: 11, italic: true, color: WHITE };
summary.getRange("A1:A26").format.columnWidth = 34;
summary.getRange("B1:B26").format.columnWidth = 18;
for (const col of ["C", "D", "E", "F", "G", "H"]) {
  summary.getRange(`${col}1:${col}26`).format.columnWidth = col === "C" ? 3 : 18;
}
summary.getRange("A6:H11").format.rowHeight = 24;
summary.getRange("A15:H20").format.rowHeight = 23;
summary.getRange("A24:H26").format.rowHeight = 34;

const summaryInspect = await workbook.inspect({
  kind: "region,formula",
  sheetId: "Summary",
  range: "A1:H26",
  maxChars: 12000,
});
await fs.writeFile(path.join(qaDir, "D11_STEM_workbook_inspect.txt"), summaryInspect.ndjson ?? String(summaryInspect));

const previewSpecs = [{ sheet: "Summary", range: "A1:H26" }, ...specs.map((spec) => ({ sheet: spec.sheet, range: spec.preview }))];
for (const previewSpec of previewSpecs) {
  const blob = await workbook.render({
    sheetName: previewSpec.sheet,
    range: previewSpec.range,
    scale: 0.8,
    headers: true,
    format: "png",
  });
  const filename = `${previewSpec.sheet.toLowerCase().replaceAll(" ", "_")}.png`;
  await fs.writeFile(path.join(previewDir, filename), new Uint8Array(await blob.arrayBuffer()));
}

const xlsx = await SpreadsheetFile.exportXlsx(workbook);
await xlsx.save(outputPath);
console.log(JSON.stringify({ outputPath, sheets: ["Summary", ...specs.map((spec) => spec.sheet)], previewDir }, null, 2));
