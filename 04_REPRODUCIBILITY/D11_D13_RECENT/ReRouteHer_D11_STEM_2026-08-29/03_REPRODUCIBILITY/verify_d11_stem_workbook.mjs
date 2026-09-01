import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";
import { fileURLToPath } from "node:url";

const workbookPath = fileURLToPath(new URL(
  "../../outputs/01a047e7-ceba-7df3-8d1a-ba8071e66430/D11_STEM_D1_Structure.xlsx",
  import.meta.url,
));

const expectedSheets = [
  "Summary",
  "Roles",
  "Role Tasks",
  "Task Ratings",
  "Role Ratings",
  "D1 Scope",
  "Sources",
  "QA Checks",
];
const expectedD1Columns = [
  "role_id", "role_title", "masco_code", "masco_title", "isco08_code", "esco_code",
  "onet_code", "task_summary", "occupation_description", "remote_possibility",
  "remote_task_count", "remote_capable_tasks", "remote_onsite_tasks", "remote_unclear_tasks",
  "remote_external_proxy", "remote_justification", "ai_exposure", "ai_exposure_share",
  "ai_exposure_external_score_0_100", "ai_exposure_measure", "flexible_role", "rating_status",
  "embedding_model", "role_embedding_384",
];

const input = await FileBlob.load(workbookPath);
const workbook = await SpreadsheetFile.importXlsx(input);
const actualSheets = [];
for (let index = 0; index < expectedSheets.length; index += 1) {
  actualSheets.push(workbook.worksheets.getItemAt(index).name);
}
if (JSON.stringify(actualSheets) !== JSON.stringify(expectedSheets)) {
  throw new Error(`Sheet order mismatch: ${JSON.stringify(actualSheets)}`);
}

const summaryValues = workbook.worksheets.getItem("Summary").getRange("B6:B11").values.flat();
const expectedSummary = [657, 5518, 653, 4, 7, 26];
if (JSON.stringify(summaryValues) !== JSON.stringify(expectedSummary)) {
  throw new Error(`Summary values mismatch: ${JSON.stringify(summaryValues)}`);
}

const rolesSheet = workbook.worksheets.getItem("Roles");
const d1Headers = rolesSheet.getRange("A1:X1").values[0];
if (JSON.stringify(d1Headers) !== JSON.stringify(expectedD1Columns)) {
  throw new Error("The first 24 Roles columns no longer match the D1 schema.");
}
const codes = rolesSheet.getRange("C2:C658").values.flat().map(String);
if (codes.length !== 657 || new Set(codes).size !== 657 || codes.some((code) => !/^\d{6}$/.test(code))) {
  throw new Error("Six-digit MASCO role-key validation failed after XLSX import.");
}
const escoCount = rolesSheet.getRange("F2:F658").values.flat().filter((value) => value !== null && value !== "").length;
const d1LineageCount = rolesSheet.getRange("AJ2:AJ658").values.flat().filter((value) => value !== null && value !== "").length;
if (escoCount !== 7 || d1LineageCount !== 26) {
  throw new Error(`Comparison/lineage counts failed: ESCO=${escoCount}, D1=${d1LineageCount}`);
}

const taskRoleIds = workbook.worksheets.getItem("Role Tasks").getRange("A2:A5519").values.flat();
if (taskRoleIds.length !== 5518 || taskRoleIds.some((value) => value === null || value === "")) {
  throw new Error("Role-task row validation failed after XLSX import.");
}
const qaStatuses = workbook.worksheets.getItem("QA Checks").getRange("D2:D7").values.flat();
if (qaStatuses.some((value) => value !== "PASS")) {
  throw new Error(`Workbook QA sheet contains a failure: ${JSON.stringify(qaStatuses)}`);
}
const summaryText = workbook.worksheets.getItem("Summary").getRange("A1:H26").values.flat();
const formulaErrors = summaryText.filter((value) => typeof value === "string" && /^#(REF!|DIV\/0!|VALUE!|NAME\?|N\/A)/.test(value));
if (formulaErrors.length > 0) {
  throw new Error(`Formula errors found: ${JSON.stringify(formulaErrors)}`);
}

console.log(JSON.stringify({
  workbook: workbookPath,
  sheets: actualSheets,
  roles: codes.length,
  tasks: taskRoleIds.length,
  sixDigitMascoCodes: true,
  escoComparisonRoles: escoCount,
  originalD1UnitGroupLineageRoles: d1LineageCount,
  qaChecks: qaStatuses,
  formulaErrors: formulaErrors.length,
}, null, 2));
