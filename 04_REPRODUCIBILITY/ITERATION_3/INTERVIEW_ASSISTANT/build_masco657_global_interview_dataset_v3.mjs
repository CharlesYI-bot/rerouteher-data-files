import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(scriptDir, "../../..");
const rawDir = path.join(projectRoot, "02_RAW_SOURCE_DATA", "ITERATION_3", "INTERVIEW_ASSISTANT");
const outputDir = path.join(projectRoot, "03_PROCESSED_DATA", "ITERATION_3", "INTERVIEW_ASSISTANT");
const previewDir = process.env.REROUTEHER_PREVIEW_DIR ?? "/tmp/rerouteher-masco657-global-v3/previews";
const outputPath = path.join(outputDir, "ReRouteHer_MASCO657_Global_Interview_Dataset_v3.xlsx");

const paths = {
  mascoCrosswalk: path.join(rawDir, "MASCO", "MASCO2020_role_crosswalk.csv"),
  escoOccupations: path.join(rawDir, "ESCO", "occupations_en.csv"),
  escoRelations: path.join(rawDir, "ESCO", "occupationSkillRelations_en.csv"),
  onetOccupations: path.join(rawDir, "ONET", "occupation_data.csv"),
  onetTasks: path.join(rawDir, "ONET", "task_statements.csv"),
  onetEssential: path.join(rawDir, "ONET", "essential_skills.csv"),
  onetTransferable: path.join(rawDir, "ONET", "transferable_skills.csv"),
  nocRoles: path.join(outputDir, "normalized", "noc_2021_v1_roles.json"),
  oscaRoles: path.join(outputDir, "normalized", "osca_2024_roles.json"),
  secondsQuestions: path.join(rawDir, "OPEN_QA", "30_seconds_questions.json"),
  secondsLicense: path.join(rawDir, "OPEN_QA", "30_seconds_LICENSE.txt"),
  continuumQuestions: path.join(rawDir, "OPEN_QA", "continuum_questions.md"),
  continuumLicense: path.join(rawDir, "OPEN_QA", "continuum_LICENSE.txt"),
  vaPage: path.join(rawDir, "OPEN_QA", "va_interview_process.html"),
};

const URLS = {
  masco: "https://www.dosm.gov.my/uploads/content-downloads/file_20220920110308.pdf",
  esco: "https://esco.ec.europa.eu/en/use-esco/download",
  escoLicense: "https://esco.ec.europa.eu/en/use-esco/download/privacy-statement",
  onet: "https://www.onetcenter.org/database.html",
  onetLicense: "https://www.onetcenter.org/license_db.html",
  noc: "https://www.statcan.gc.ca/en/subjects/standard/noc/2021/indexV1",
  nocLicense: "https://www.statcan.gc.ca/en/terms-conditions/open-licence",
  osca: "https://www.abs.gov.au/statistics/classifications/osca-occupation-standard-classification-australia/2024-version-1-0/data-downloads",
  oscaLicense: "https://www.abs.gov.au/website-privacy-copyright-and-disclaimer",
  seconds: "https://github.com/Chalarangelo/30-seconds-of-interviews/tree/da235b6185721161b7ebc413075b76dc70339ccf",
  continuum: "https://github.com/ContinuumIO/interview-questions/tree/a22ec7982062ce5c3bad162495452e5738ae3220",
  opm: "https://www.opm.gov/policy-data-oversight/assessment-and-selection/structured-interviews/",
  va: "https://vacareers.va.gov/job-application-process/the-interview-process/",
};

function parseCsv(text) {
  const rows = [];
  let row = [];
  let field = "";
  let quoted = false;
  for (let i = 0; i < text.length; i += 1) {
    const ch = text[i];
    if (quoted) {
      if (ch === '"') {
        if (text[i + 1] === '"') {
          field += '"';
          i += 1;
        } else quoted = false;
      } else field += ch;
    } else if (ch === '"') quoted = true;
    else if (ch === ",") {
      row.push(field);
      field = "";
    } else if (ch === "\n") {
      row.push(field.replace(/\r$/, ""));
      rows.push(row);
      row = [];
      field = "";
    } else field += ch;
  }
  if (field.length || row.length) {
    row.push(field.replace(/\r$/, ""));
    rows.push(row);
  }
  const headers = rows.shift() ?? [];
  return rows
    .filter((values) => values.some((value) => value !== ""))
    .map((values) => Object.fromEntries(headers.map((header, index) => [header, values[index] ?? ""])));
}

async function loadCsv(file) {
  return parseCsv(await fs.readFile(file, "utf8"));
}

async function loadJson(file) {
  return JSON.parse(await fs.readFile(file, "utf8"));
}

async function sha256(file) {
  return crypto.createHash("sha256").update(await fs.readFile(file)).digest("hex");
}

function clean(value, max = 32000) {
  const text = String(value ?? "").replace(/\s+/g, " ").trim();
  return text.length > max ? `${text.slice(0, max - 20)} … [truncated]` : text;
}

function norm(value) {
  return clean(value)
    .toLowerCase()
    .normalize("NFKD")
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

function cleanAnchor(value) {
  let text = clean(value, 1400).replace(/^[•,;:.\-\s]+|[;,\s]+$/g, "");
  text = text.replace(/^and\s+/i, "").replace(/^to\s+/i, "");
  return text || "the role's core responsibilities";
}

function isMeaningfulAnchor(value) {
  const text = norm(value);
  if (text.length < 4) return false;
  return !/^(this group performs|this unit group performs|the following duties|main duties|employment requirements)(\s|$)/.test(text);
}

function compactCode(value) {
  return String(value ?? "").replace(/[^0-9]/g, "");
}

function uniqueBy(items, keyFn) {
  const seen = new Set();
  return items.filter((item) => {
    const key = keyFn(item);
    if (!key || seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function colLetter(index) {
  let n = index + 1;
  let result = "";
  while (n > 0) {
    n -= 1;
    result = String.fromCharCode(65 + (n % 26)) + result;
    n = Math.floor(n / 26);
  }
  return result;
}

function parseNumber(value, fallback = 0) {
  const number = Number(value);
  return Number.isFinite(number) ? number : fallback;
}

function stemToken(token) {
  if (token.endsWith("ies") && token.length > 5) return `${token.slice(0, -3)}y`;
  if (token.endsWith("s") && !token.endsWith("ss") && token.length > 4) return token.slice(0, -1);
  return token;
}

const stopTokens = new Set(["and", "or", "the", "of", "for", "in", "to", "a", "an"]);
function titleTokens(value) {
  return norm(value)
    .split(" ")
    .filter((token) => token && !stopTokens.has(token))
    .map(stemToken);
}

function titleSimilarity(left, right) {
  const leftNorm = norm(left);
  const rightNorm = norm(right);
  if (!leftNorm || !rightNorm) return { score: 0, shared: 0, exact: false };
  if (leftNorm === rightNorm) return { score: 1, shared: titleTokens(left).length, exact: true };
  const a = new Set(titleTokens(left));
  const b = new Set(titleTokens(right));
  let shared = 0;
  for (const token of a) if (b.has(token)) shared += 1;
  const dice = (2 * shared) / Math.max(a.size + b.size, 1);
  const phraseContainment = leftNorm.includes(rightNorm) || rightNorm.includes(leftNorm);
  const score = phraseContainment && shared >= 2 ? Math.max(dice, 0.82) : dice;
  return { score, shared, exact: false };
}

function bestTitleMatch(title, candidates) {
  let best = null;
  for (const candidate of candidates) {
    const similarity = titleSimilarity(title, candidate.title);
    if (!best || similarity.score > best.score) best = { ...candidate, ...similarity };
  }
  if (!best) return null;
  const accepted = best.exact || best.score >= 0.72 || (best.score >= 0.62 && best.shared >= 2);
  if (!accepted) return null;
  return { ...best, confidence: best.exact || best.score >= 0.82 ? "high" : "medium" };
}

function parseContinuum(markdown) {
  const records = [];
  let section = "Introduction";
  let current = null;
  const flush = () => {
    if (!current) return;
    records.push({ section: current.section, question: clean(current.lines.join(" ")) });
    current = null;
  };
  for (const line of markdown.split(/\r?\n/)) {
    const heading = line.match(/^#{3,4}\s+(.+?)\s*$/);
    if (heading) {
      flush();
      section = clean(heading[1]);
      continue;
    }
    const question = line.match(/^\s*\d+\.\s+(.+)$/);
    if (question) {
      flush();
      current = { section, lines: [question[1]] };
      continue;
    }
    if (current && line.trim()) current.lines.push(line.trim());
    if (current && !line.trim()) flush();
  }
  flush();
  return records;
}

const [
  mascoCrosswalk,
  escoOccupationsRaw,
  escoRelations,
  onetOccupations,
  onetTasks,
  onetEssential,
  onetTransferable,
  nocRoles,
  oscaRoles,
  secondsQuestions,
  continuumMarkdown,
] = await Promise.all([
  loadCsv(paths.mascoCrosswalk),
  loadCsv(paths.escoOccupations),
  loadCsv(paths.escoRelations),
  loadCsv(paths.onetOccupations),
  loadCsv(paths.onetTasks),
  loadCsv(paths.onetEssential),
  loadCsv(paths.onetTransferable),
  loadJson(paths.nocRoles),
  loadJson(paths.oscaRoles),
  loadJson(paths.secondsQuestions),
  fs.readFile(paths.continuumQuestions, "utf8"),
]);

const escoOccupations = uniqueBy(escoOccupationsRaw, (row) => row.conceptUri);
const escoByCode = new Map(escoOccupations.map((row) => [row.code, row]));
const escoByTitle = new Map(escoOccupations.map((row) => [norm(row.preferredLabel), row]));

const escoSkillMap = new Map();
for (const relation of escoRelations) {
  if (!escoSkillMap.has(relation.occupationUri)) escoSkillMap.set(relation.occupationUri, []);
  escoSkillMap.get(relation.occupationUri).push({
    anchor_type: "skill",
    anchor_text: cleanAnchor(relation.skillLabel),
    source_standard: "ESCO 1.2.1",
    source_record_id: relation.skillUri,
    source_url: URLS.esco,
    license_id: "EC-REUSE-ESCO",
    relation_type: relation.relationType,
  });
}
for (const [uri, list] of escoSkillMap) {
  escoSkillMap.set(
    uri,
    uniqueBy(
      list.sort((a, b) => (a.relation_type === "essential" ? 0 : 1) - (b.relation_type === "essential" ? 0 : 1) || a.anchor_text.localeCompare(b.anchor_text)),
      (item) => norm(item.anchor_text),
    ),
  );
}

const onetTaskMap = new Map();
for (const task of onetTasks) {
  const code = task["O*NET-SOC Code"];
  if (!onetTaskMap.has(code)) onetTaskMap.set(code, []);
  onetTaskMap.get(code).push({
    anchor_type: "task",
    anchor_text: cleanAnchor(task.Task),
    source_standard: "O*NET 31.0",
    source_record_id: `${code}|task:${task["Task ID"]}`,
    source_url: URLS.onet,
    license_id: "CC-BY-4.0-ONET",
    task_type: task["Task Type"],
  });
}
for (const list of onetTaskMap.values()) {
  list.sort((a, b) => (a.task_type === "Core" ? 0 : 1) - (b.task_type === "Core" ? 0 : 1));
}

const onetSkillMap = new Map();
for (const skill of [...onetEssential, ...onetTransferable]) {
  if (skill["Scale ID"] !== "IM" || /^(y|true|1)$/i.test(skill["Recommend Suppress"] ?? "")) continue;
  const code = skill["O*NET-SOC Code"];
  if (!onetSkillMap.has(code)) onetSkillMap.set(code, []);
  onetSkillMap.get(code).push({
    anchor_type: "skill",
    anchor_text: cleanAnchor(skill["Element Name"]),
    source_standard: "O*NET 31.0",
    source_record_id: `${code}|skill:${skill["Element ID"]}`,
    source_url: URLS.onet,
    license_id: "CC-BY-4.0-ONET",
    importance: Math.round(((parseNumber(skill["Data Value"], 1) - 1) / 4) * 100),
  });
}
for (const [code, list] of onetSkillMap) {
  onetSkillMap.set(code, uniqueBy(list.sort((a, b) => b.importance - a.importance), (item) => norm(item.anchor_text)));
}

const onetCandidates = onetOccupations.map((row) => ({
  code: row["O*NET-SOC Code"],
  title: clean(row.Title),
  description: clean(row.Description),
  source_standard: "O*NET 31.0",
  source_url: URLS.onet,
  license_id: "CC-BY-4.0-ONET",
}));
const nocCandidates = nocRoles.map((row) => ({
  code: row.code,
  title: clean(row.title),
  description: clean((row.main_duties ?? []).slice(0, 3).join("; ")),
  row,
  source_standard: "NOC 2021 Version 1.0",
  source_url: URLS.noc,
  license_id: "STATCAN-OPEN-LICENCE",
}));
const oscaCandidates = oscaRoles.map((row) => ({
  code: row.code,
  title: clean(row.title),
  description: clean(row.description),
  row,
  source_standard: "OSCA 2024 Version 1.0",
  source_url: URLS.osca,
  license_id: "CC-BY-4.0-ABS",
}));

const mascoGroups = new Map();
for (const row of mascoCrosswalk) {
  if (!row.source_current_role_id) continue;
  if (!mascoGroups.has(row.source_current_role_id)) mascoGroups.set(row.source_current_role_id, []);
  mascoGroups.get(row.source_current_role_id).push(row);
}

function chooseMascoRow(rows) {
  return [...rows].sort((a, b) => {
    const score = (row) =>
      (row.status === "retained" ? 8 : 0) +
      (row.primary_profile_for_target === "true" ? 4 : 0) +
      (row.remap_confidence === "high" ? 2 : row.remap_confidence === "medium" ? 1 : 0) +
      (row.source_esco_code ? 1 : 0);
    return score(b) - score(a);
  })[0];
}

const roles = [];
const matches = [];
const anchorsByRole = new Map();
const roleAnchors = [];

function addMatch(role, sourceStandard, sourceCode, sourceTitle, sourceUrl, licenseId, method, score, confidence, recordId, description) {
  matches.push({
    match_id: `${role.role_id}-M${String((role.match_ordinal ?? 0) + 1).padStart(2, "0")}`,
    role_id: role.role_id,
    masco_code: role.masco_code,
    masco_title: role.role_title,
    global_source_standard: sourceStandard,
    global_source_code: sourceCode,
    global_source_title: sourceTitle,
    mapping_method: method,
    title_similarity_0_100: Math.round(score * 100),
    mapping_confidence: confidence,
    source_record_id: recordId || sourceCode,
    source_url: sourceUrl,
    license_id: licenseId,
    source_description: description,
    review_status: method === "MASCO_crosswalk" ? "crosswalk_reviewed_in_source_project" : "human_mapping_review_required",
  });
  role.match_ordinal = (role.match_ordinal ?? 0) + 1;
}

function balancedAnchors(allAnchors, limit = 14) {
  const deduped = uniqueBy(allAnchors.filter((anchor) => isMeaningfulAnchor(anchor.anchor_text)), (anchor) => norm(anchor.anchor_text));
  const grouped = new Map();
  for (const anchor of deduped) {
    if (!grouped.has(anchor.source_standard)) grouped.set(anchor.source_standard, []);
    grouped.get(anchor.source_standard).push(anchor);
  }
  const result = [];
  let rank = 0;
  while (result.length < limit) {
    let added = false;
    for (const list of grouped.values()) {
      if (list[rank]) {
        result.push(list[rank]);
        added = true;
        if (result.length === limit) break;
      }
    }
    if (!added) break;
    rank += 1;
  }
  return result;
}

for (const [sourceRoleId, rows] of mascoGroups) {
  const selected = chooseMascoRow(rows);
  const role = {
    role_id: sourceRoleId,
    masco_code: compactCode(selected.source_current_masco_code),
    role_title: clean(selected.source_current_role_title),
    locale: "en-MY",
    role_standard: "MASCO 2020",
    role_source_url: selected.masco2020_source_url || URLS.masco,
    role_license_status: "official_source_rights_review_required_for_external_bulk_redistribution",
    crosswalk_status: selected.status || "",
    crosswalk_confidence: selected.remap_confidence || "",
    mapped_masco2020_code: selected.masco2020_code || "",
    mapped_masco2020_title: selected.masco2020_title || "",
    match_ordinal: 0,
  };
  const roleAnchorCandidates = [];

  const esco = escoByCode.get(selected.source_esco_code) ?? escoByTitle.get(norm(selected.source_esco_title));
  if (esco) {
    addMatch(role, "ESCO 1.2.1", esco.code, esco.preferredLabel, URLS.esco, "EC-REUSE-ESCO", "MASCO_crosswalk", 1, selected.remap_confidence || "high", esco.conceptUri, clean(esco.description || esco.definition));
    roleAnchorCandidates.push(...(escoSkillMap.get(esco.conceptUri) ?? []).slice(0, 6));
  }

  const onet = bestTitleMatch(role.role_title, onetCandidates);
  if (onet) {
    addMatch(role, onet.source_standard, onet.code, onet.title, onet.source_url, onet.license_id, "title_similarity", onet.score, onet.confidence, onet.code, onet.description);
    roleAnchorCandidates.push(...(onetTaskMap.get(onet.code) ?? []).slice(0, 4));
    roleAnchorCandidates.push(...(onetSkillMap.get(onet.code) ?? []).slice(0, 3));
  }

  const noc = bestTitleMatch(role.role_title, nocCandidates);
  if (noc) {
    addMatch(role, noc.source_standard, noc.code, noc.title, noc.source_url, noc.license_id, "title_similarity", noc.score, noc.confidence, noc.code, noc.description);
    roleAnchorCandidates.push(...(noc.row.main_duties ?? []).slice(0, 4).map((text, index) => ({
      anchor_type: "duty",
      anchor_text: cleanAnchor(text),
      source_standard: noc.source_standard,
      source_record_id: `${noc.code}|main-duty:${index + 1}`,
      source_url: noc.source_url,
      license_id: noc.license_id,
    })));
    roleAnchorCandidates.push(...(noc.row.employment_requirements ?? []).slice(0, 2).map((text, index) => ({
      anchor_type: "requirement",
      anchor_text: cleanAnchor(text),
      source_standard: noc.source_standard,
      source_record_id: `${noc.code}|requirement:${index + 1}`,
      source_url: noc.source_url,
      license_id: noc.license_id,
    })));
  }

  const osca = bestTitleMatch(role.role_title, oscaCandidates);
  if (osca) {
    addMatch(role, osca.source_standard, osca.code, osca.title, osca.source_url, osca.license_id, "title_similarity", osca.score, osca.confidence, osca.code, osca.description);
    roleAnchorCandidates.push(...(osca.row.tasks ?? []).slice(0, 4).map((text, index) => ({
      anchor_type: "task",
      anchor_text: cleanAnchor(text),
      source_standard: osca.source_standard,
      source_record_id: `${osca.code}|task:${index + 1}`,
      source_url: osca.source_url,
      license_id: osca.license_id,
    })));
    if (osca.row.skill_attributes) roleAnchorCandidates.push({
      anchor_type: "skill",
      anchor_text: cleanAnchor(osca.row.skill_attributes),
      source_standard: osca.source_standard,
      source_record_id: `${osca.code}|skill-attributes`,
      source_url: osca.source_url,
      license_id: osca.license_id,
    });
  }

  const selectedAnchors = balancedAnchors(roleAnchorCandidates);
  anchorsByRole.set(role.role_id, selectedAnchors);
  selectedAnchors.forEach((anchor, index) => roleAnchors.push({
    anchor_id: `${role.role_id}-A${String(index + 1).padStart(2, "0")}`,
    role_id: role.role_id,
    masco_code: role.masco_code,
    role_title: role.role_title,
    anchor_rank: index + 1,
    ...anchor,
  }));
  role.global_match_count = role.match_ordinal;
  role.global_anchor_count = selectedAnchors.length;
  role.global_sources = [...new Set(selectedAnchors.map((anchor) => anchor.source_standard))].join("; ");
  role.question_count = 12;
  delete role.match_ordinal;
  roles.push(role);
}

roles.sort((a, b) => a.masco_code.localeCompare(b.masco_code) || a.role_title.localeCompare(b.role_title));
matches.sort((a, b) => a.role_id.localeCompare(b.role_id) || a.global_source_standard.localeCompare(b.global_source_standard));
roleAnchors.sort((a, b) => a.role_id.localeCompare(b.role_id) || a.anchor_rank - b.anchor_rank);

if (roles.length !== 657) throw new Error(`Expected exactly 657 MASCO roles, found ${roles.length}`);
console.log(`Built ${roles.length} MASCO roles with ${matches.length} global matches and ${roleAnchors.length} anchors`);

const frameworks = {
  introduction: ["concise-summary", "State your current professional focus, two relevant strengths, one evidence point, and why those fit this role."],
  motivation: ["motivation-fit-evidence", "Connect your motivation to the work, show that you understand the role, and support the fit with evidence."],
  behavioural: ["STAR", "Describe the situation and your responsibility, explain your own actions and decisions, then give the result and learning."],
  technical: ["approach-controls-evidence", "Explain the method step by step, name standards or checks, discuss trade-offs, and show how you validate the result."],
  situational: ["assess-act-communicate-review", "Clarify facts, prioritise risk, act within authority, communicate, escalate when needed, and confirm resolution."],
  career_growth: ["capability-gap-plan", "Identify one relevant capability, explain why it matters, and give a specific learning and application plan."],
  employer_question: ["informed-question", "Ask a concise question about expectations, measures of success, support, or near-term priorities."],
};

function pickDistinctAnchors(roleId, count) {
  const sourceAnchors = anchorsByRole.get(roleId) ?? [];
  const selected = [];
  const seen = new Set();
  for (const anchor of sourceAnchors) {
    const key = norm(anchor.anchor_text);
    if (!key || seen.has(key)) continue;
    seen.add(key);
    selected.push(anchor);
    if (selected.length === count) break;
  }
  while (selected.length < count) {
    selected.push({
      anchor_type: "role_title",
      anchor_text: roles.find((role) => role.role_id === roleId)?.role_title ?? "the role",
      source_standard: "MASCO 2020",
      source_record_id: roleId,
      source_url: URLS.masco,
      license_id: "MASCO-RIGHTS-REVIEW",
    });
  }
  return selected;
}

function questionSet(role) {
  const a = pickDistinctAnchors(role.role_id, 8);
  return [
    { category: "introduction", difficulty: "foundation", anchor: null, text: `Give me a concise overview of your experience and explain how it prepares you for the ${role.role_title} role.`, follow_up: "Which achievement best demonstrates your readiness?" },
    { category: "motivation", difficulty: "foundation", anchor: null, text: `Why are you interested in the ${role.role_title} role, and what value would you aim to deliver in the first six months?`, follow_up: "What would you need to learn first?" },
    { category: "behavioural", difficulty: "intermediate", anchor: a[0], text: `Tell me about a time your work involved this responsibility: ${a[0].anchor_text}. What did you do, and what changed as a result?`, follow_up: "What evidence shows that your action made a difference?" },
    { category: "behavioural", difficulty: "advanced", anchor: a[1], text: `Describe a difficult decision connected to: ${a[1].anchor_text}. How did you evaluate the options and consequences?`, follow_up: "What would you do differently now?" },
    { category: "behavioural", difficulty: "intermediate", anchor: a[2], text: `Give an example of working with other people while responsible for: ${a[2].anchor_text}. How did you handle different expectations?`, follow_up: "How did you confirm alignment?" },
    { category: "technical", difficulty: "intermediate", anchor: a[3], text: `Walk me through your approach to this area of work: ${a[3].anchor_text}. What steps, tools, or standards would you use?`, follow_up: "How would you validate the result?" },
    { category: "technical", difficulty: "advanced", anchor: a[4], text: `What controls and quality checks would you apply when handling: ${a[4].anchor_text}? Explain the main trade-offs.`, follow_up: "Which failure mode would concern you most?" },
    { category: "technical", difficulty: "advanced", anchor: a[5], text: `How would you measure performance and improve the way this work is done: ${a[5].anchor_text}?`, follow_up: "What data would you trust, and what are its limitations?" },
    { category: "situational", difficulty: "intermediate", anchor: a[6], text: `A priority changes while you are responsible for: ${a[6].anchor_text}. How would you reassess, communicate, and deliver?`, follow_up: "What would cause you to escalate?" },
    { category: "situational", difficulty: "advanced", anchor: a[7], text: `You notice a quality, safety, or compliance risk related to: ${a[7].anchor_text}. What would you do first, and why?`, follow_up: "How would you document and close the issue?" },
    { category: "career_growth", difficulty: "foundation", anchor: null, text: `Which capability would you most need to strengthen to excel as a ${role.role_title}, and how would you develop it?`, follow_up: "How would you demonstrate progress?" },
    { category: "employer_question", difficulty: "foundation", anchor: null, text: `What would you ask the interviewer to understand how success is measured for the ${role.role_title} role?`, follow_up: "How would the answer influence your priorities?" },
  ];
}

const questions = [];
const questionCountByRole = new Map();
const duplicateQuestionKeys = new Set();
for (const role of roles) {
  questionSet(role).forEach((item, index) => {
    const anchor = item.anchor ?? {
      anchor_type: "role_title",
      anchor_text: role.role_title,
      source_standard: "MASCO 2020",
      source_record_id: role.role_id,
      source_url: role.role_source_url,
      license_id: "MASCO-RIGHTS-REVIEW",
    };
    const [answerFramework, answerGuidance] = frameworks[item.category];
    const key = `${role.role_id}|${norm(item.text)}`;
    if (duplicateQuestionKeys.has(key)) throw new Error(`Duplicate role question: ${key}`);
    duplicateQuestionKeys.add(key);
    questionCountByRole.set(role.role_id, (questionCountByRole.get(role.role_id) ?? 0) + 1);
    const grounded = anchor.source_standard !== "MASCO 2020";
    questions.push({
      question_id: `${role.role_id}-GQ${String(index + 1).padStart(2, "0")}`,
      role_id: role.role_id,
      masco_code: role.masco_code,
      role_title: role.role_title,
      locale: role.locale,
      category: item.category,
      difficulty: item.difficulty,
      question_text: item.text,
      anchor_type: anchor.anchor_type,
      anchor_text: anchor.anchor_text,
      global_anchor_standard: anchor.source_standard,
      global_anchor_record_id: anchor.source_record_id,
      global_anchor_url: anchor.source_url,
      global_anchor_license_id: anchor.license_id,
      interview_method_sources: "OPM-STRUCTURED-INTERVIEWS; VA-PBI",
      authoring_method: grounded ? "generated_from_global_official_role_anchor" : "generated_from_MASCO_role_title_and_global_structured_interview_method",
      answer_framework: answerFramework,
      answer_guidance: answerGuidance,
      strong_evidence_signals: "Specific context; clear personal contribution; credible reasoning; job-relevant controls; evidenced result; reflection.",
      watch_out_for: "Generic answer; unclear ownership; unsupported claim; unsafe shortcut; no result, validation, or learning.",
      follow_up_question: item.follow_up,
      quality_score_100: grounded ? 88 : 78,
      review_status: "human_domain_fairness_and_legal_review_required",
      safety_note: "Score only job-relevant evidence. Do not use protected or personal characteristics.",
    });
  });
}

const openQa = [];
secondsQuestions.forEach((item, index) => openQa.push({
  qa_id: `OPEN-30S-${String(index + 1).padStart(3, "0")}`,
  source_id: "GITHUB-30SECONDS-INTERVIEWS",
  source_record_id: clean(item.name || `record-${index + 1}`),
  topic_or_section: clean((item.tags ?? []).join("; ")),
  expertise: clean(item.expertise),
  question_text: clean(item.question),
  source_answer: clean(item.answer),
  good_to_hear: clean(Array.isArray(item.goodToHear) ? item.goodToHear.join("; ") : item.goodToHear),
  answer_status: item.answer ? "source_answer_present" : "no_source_answer",
  active_for_practice: "yes_after_technical_currentness_review",
  currentness_status: "archived_repository_manual_review_required",
  license_id: "MIT-30SECONDS",
  source_url: URLS.seconds,
  attribution: "30 Seconds of Interviews, © 2018 Stefan Feješ, MIT License.",
  review_note: "Validate language, framework, vendor, and version assumptions before use.",
}));

const continuumRecords = parseContinuum(continuumMarkdown);
continuumRecords.forEach((item, index) => {
  const excluded = item.section === "Things We Would Never Ask";
  openQa.push({
    qa_id: `OPEN-CONT-${String(index + 1).padStart(3, "0")}`,
    source_id: "GITHUB-CONTINUUM-INTERVIEW-QUESTIONS",
    source_record_id: `${norm(item.section).replace(/ /g, "-")}-${index + 1}`,
    topic_or_section: item.section,
    expertise: "not specified",
    question_text: item.question,
    source_answer: "",
    good_to_hear: "",
    answer_status: "question_only",
    active_for_practice: excluded ? "no" : "yes_after_technical_currentness_review",
    currentness_status: "manual_review_required",
    license_id: "CC-BY-SA-4.0-CONTINUUM",
    source_url: URLS.continuum,
    attribution: "Interview Questions by Continuum Analytics, Inc., CC BY-SA 4.0.",
    review_note: excluded ? "Source labels this item as a question it would never ask; retained only for context." : "Add a domain-reviewed answer and scoring key before production use.",
  });
});

function preferredOpenQaTopics(roleTitle) {
  const value = norm(roleTitle);
  const topics = [];
  if (/database|data base|dba/.test(value)) topics.push("relational databases");
  if (/front end|frontend|web developer|web programmer|web designer/.test(value)) topics.push("javascript", "react", "html", "css", "accessibility", "software engineering questions");
  if (/software|programmer|developer|application|computer system|information technology/.test(value)) topics.push("javascript", "node", "software engineering questions");
  if (/cyber|security/.test(value)) topics.push("security", "software engineering questions");
  if (/data scientist|data analyst|data engineer|statistician/.test(value)) topics.push("relational databases", "software engineering questions");
  return [...new Set(topics)];
}

const openQaLinks = [];
for (const role of roles) {
  const topics = preferredOpenQaTopics(role.role_title);
  if (!topics.length) continue;
  const candidates = openQa.filter((record) => record.active_for_practice.startsWith("yes") && topics.some((topic) => norm(record.topic_or_section).includes(norm(topic))));
  uniqueBy(candidates, (record) => record.qa_id).slice(0, 8).forEach((record, index) => openQaLinks.push({
    link_id: `${role.role_id}-OQ${String(index + 1).padStart(2, "0")}`,
    role_id: role.role_id,
    masco_code: role.masco_code,
    role_title: role.role_title,
    qa_id: record.qa_id,
    qa_source_id: record.source_id,
    qa_topic: record.topic_or_section,
    question_text: record.question_text,
    relevance_rule: `Role-title keyword matched global Q&A topic: ${topics.join(", ")}`,
    license_id: record.license_id,
    source_url: record.source_url,
    review_status: "human_relevance_and_currentness_review_required",
  }));
}

const roleQuestionCount = questions.length;
const sourceFiles = [paths.mascoCrosswalk, paths.escoOccupations, paths.escoRelations, paths.onetOccupations, paths.onetTasks, paths.onetEssential, paths.onetTransferable, paths.nocRoles, paths.oscaRoles, paths.secondsQuestions, paths.secondsLicense, paths.continuumQuestions, paths.continuumLicense, paths.vaPage];
const checksums = Object.fromEntries(await Promise.all(sourceFiles.map(async (file) => [file, await sha256(file)])));

const sources = [
  { source_id: "MASCO-2020", name: "Malaysia Standard Classification of Occupations 2020", publisher: "Department of Statistics Malaysia / Ministry of Human Resources", version: "2020", source_use: "Defines the only 657 roles in this workbook", source_url: URLS.masco, licence: "No explicit open-data licence confirmed for bulk redistribution in supplied files", licence_url: URLS.masco, production_eligibility: "rights_review_required_before_external_bulk_release", attribution_or_obligation: "Keep MASCO-derived role rows separable and confirm permission before external redistribution.", quality_note: "Official Malaysian role standard; no global roles are added." },
  { source_id: "ESCO-1.2.1", name: "European Skills, Competences, Qualifications and Occupations", publisher: "European Commission", version: "1.2.1", source_use: "Global occupation and skill enrichment mapped to MASCO roles", source_url: URLS.esco, licence: "European Commission reuse policy / Decision 2011/833/EU", licence_url: URLS.escoLicense, production_eligibility: "eligible_with_acknowledgement_and_modification_notice", attribution_or_obligation: "Acknowledge the European Union and ESCO version; indicate adaptations.", quality_note: "Direct project crosswalk is preferred over title matching." },
  { source_id: "ONET-31.0", name: "O*NET Database", publisher: "U.S. Department of Labor, Employment and Training Administration", version: "31.0", source_use: "Global task and skill enrichment mapped to MASCO roles", source_url: URLS.onet, licence: "Creative Commons Attribution 4.0 International", licence_url: URLS.onetLicense, production_eligibility: "eligible_with_attribution_and_modification_notice", attribution_or_obligation: "Credit O*NET 31.0 and U.S. DOL/ETA; identify adaptations; do not imply endorsement.", quality_note: "Title-similarity matches require human review." },
  { source_id: "NOC-2021-V1", name: "National Occupational Classification 2021 Version 1.0", publisher: "Statistics Canada and Employment and Social Development Canada", version: "2021 Version 1.0", source_use: "Global duty and requirement enrichment mapped to MASCO roles", source_url: URLS.noc, licence: "Statistics Canada Open Licence", licence_url: URLS.nocLicense, production_eligibility: "eligible_with_attribution", attribution_or_obligation: "Identify Statistics Canada as source and describe adaptations.", quality_note: "Title-similarity matches require human review." },
  { source_id: "OSCA-2024-V1", name: "Occupation Standard Classification for Australia", publisher: "Australian Bureau of Statistics", version: "2024 Version 1.0", source_use: "Global task and skill enrichment mapped to MASCO roles", source_url: URLS.osca, licence: "Creative Commons Attribution 4.0 International, subject to ABS exclusions", licence_url: URLS.oscaLicense, production_eligibility: "eligible_with_attribution_and_exclusion_check", attribution_or_obligation: "Attribute the Australian Bureau of Statistics; check excluded third-party material and logos.", quality_note: "Title-similarity matches require human review." },
  { source_id: "GITHUB-30SECONDS-INTERVIEWS", name: "30 Seconds of Interviews", publisher: "Stefan Feješ and contributors", version: "commit da235b6185721161b7ebc413075b76dc70339ccf", source_use: "Open technical interview Q&A and role links", source_url: URLS.seconds, licence: "MIT License", licence_url: `${URLS.seconds}/LICENSE`, production_eligibility: "eligible_with_notice_and_technical_currentness_review", attribution_or_obligation: "Preserve the MIT copyright and permission notice.", quality_note: "Archived source; technical currentness review is mandatory." },
  { source_id: "GITHUB-CONTINUUM-INTERVIEW-QUESTIONS", name: "Continuum Analytics Interview Questions", publisher: "Continuum Analytics, Inc.", version: "commit a22ec7982062ce5c3bad162495452e5738ae3220", source_use: "Open technical interview questions and role links", source_url: URLS.continuum, licence: "Creative Commons Attribution-ShareAlike 4.0 International", licence_url: "https://creativecommons.org/licenses/by-sa/4.0/", production_eligibility: "eligible_with_attribution_and_share_alike", attribution_or_obligation: "Attribute Continuum Analytics and apply compatible share-alike terms to adaptations.", quality_note: "Question-only source; five 'never ask' records remain disabled." },
  { source_id: "OPM-STRUCTURED-INTERVIEWS", name: "Structured Interviews", publisher: "U.S. Office of Personnel Management", version: "web guidance", source_use: "Structured-question and scoring methodology", source_url: URLS.opm, licence: "U.S. federal guidance; verify page-specific reuse terms for copied content", licence_url: URLS.opm, production_eligibility: "methodology_reference_only", attribution_or_obligation: "Cite OPM when describing its structured-interview guidance.", quality_note: "Methodology used; no bulk OPM question corpus copied." },
  { source_id: "VA-PBI", name: "Performance-Based Interviewing / The interview process", publisher: "U.S. Department of Veterans Affairs", version: "page modified 2026-06-16", source_use: "PBI and STAR answer methodology", source_url: URLS.va, licence: "U.S. federal guidance; verify page-specific reuse terms for copied content", licence_url: "https://www.va.gov/web/standards/disclaimer.cfm", production_eligibility: "methodology_reference_only", attribution_or_obligation: "Cite VA when describing its PBI/STAR guidance.", quality_note: "Methodology used; verbatim VA examples are not redistributed." },
];

const sourceCoverage = ["ESCO 1.2.1", "O*NET 31.0", "NOC 2021 Version 1.0", "OSCA 2024 Version 1.0"].map((standard) => ({
  global_source_standard: standard,
  matched_masco_roles: new Set(matches.filter((match) => match.global_source_standard === standard).map((match) => match.role_id)).size,
  match_records: matches.filter((match) => match.global_source_standard === standard).length,
  anchor_records: roleAnchors.filter((anchor) => anchor.source_standard === standard).length,
  mapping_method: standard === "ESCO 1.2.1" ? "MASCO project crosswalk" : "conservative English title similarity",
  review_requirement: standard === "ESCO 1.2.1" ? "Review crosswalk status and confidence" : "Human mapping review required",
}));

const categoryMix = ["introduction", "motivation", "behavioural", "technical", "situational", "career_growth", "employer_question"].map((category) => ({
  category,
  questions_per_role: questions.filter((question) => question.role_id === roles[0].role_id && question.category === category).length,
  total_questions: questions.filter((question) => question.category === category).length,
}));

const coverageRows = roles.map((role) => ({
  role_id: role.role_id,
  masco_code: role.masco_code,
  role_title: role.role_title,
  expected_questions: 12,
  actual_questions: "",
  expected_global_matches_minimum: 1,
  actual_global_matches: "",
  actual_global_anchors: "",
  linked_open_qa_records: "",
  qa_status: "",
}));

const qualityChecks = [];
function addCheck(check_id, check, expected, actual, evidence) {
  qualityChecks.push({ check_id, check, expected, actual, status: String(expected) === String(actual) ? "PASS" : "FAIL", evidence });
}
addCheck("DQ-01", "Exactly 657 MASCO roles", 657, roles.length, "MASCO Roles.role_id");
addCheck("DQ-02", "Unique MASCO role IDs", 657, new Set(roles.map((role) => role.role_id)).size, "MASCO Roles.role_id");
addCheck("DQ-03", "Unique role-question IDs", questions.length, new Set(questions.map((question) => question.question_id)).size, "Interview Q&A.question_id");
addCheck("DQ-04", "Twelve interview questions per role", 657, [...questionCountByRole.values()].filter((count) => count === 12).length, "Coverage formulas recalculate in Excel");
addCheck("DQ-05", "No duplicate normalized question within a role", 0, questions.length - duplicateQuestionKeys.size, "role_id + normalized question_text");
addCheck("DQ-06", "Every question has source lineage", questions.length, questions.filter((question) => question.global_anchor_url && question.interview_method_sources).length, "Interview Q&A source columns");
addCheck("DQ-07", "Every role has at least one global match", 657, roles.filter((role) => role.global_match_count >= 1).length, "Global Matches.role_id");
addCheck("DQ-08", "Open Q&A records retained with licence IDs", openQa.length, openQa.filter((record) => record.license_id).length, "Open Q&A.license_id");
addCheck("DQ-09", "Source-designated 'never ask' records disabled", 5, openQa.filter((record) => record.active_for_practice === "no").length, "Continuum source section");
addCheck("DQ-10", "Source file checksums captured", sourceFiles.length, Object.values(checksums).filter(Boolean).length, "SHA-256 at build");
addCheck("DQ-11", "Structural classification headings excluded from anchors", 0, roleAnchors.filter((anchor) => !isMeaningfulAnchor(anchor.anchor_text)).length, "Role Anchors.anchor_text");

const rubricRows = [
  { dimension: "Relevance", definition: "Evidence directly addresses the question and the MASCO role.", score_1: "Mostly unrelated or generic.", score_3: "Relevant example with some missing detail.", score_5: "Role-specific evidence with clear scope and context." },
  { dimension: "Ownership", definition: "Candidate makes their own contribution and decisions clear.", score_1: "Contribution cannot be separated from the team.", score_3: "Personal actions are stated but rationale is limited.", score_5: "Actions, judgment, and collaboration boundaries are explicit." },
  { dimension: "Method", definition: "Approach is structured, safe, and technically credible.", score_1: "Unstructured or unsafe approach.", score_3: "Generally sound approach with incomplete controls.", score_5: "Clear sequence, trade-offs, controls, and escalation points." },
  { dimension: "Outcome", definition: "Response explains the result and how it was verified.", score_1: "No result or only assertion.", score_3: "Result described but weakly evidenced.", score_5: "Specific, evidenced result linked to the candidate's action." },
  { dimension: "Reflection", definition: "Candidate identifies learning and how it changes future action.", score_1: "No learning or defensive response.", score_3: "General lesson stated.", score_5: "Specific learning, limitation, and improved future approach." },
  { dimension: "Communication", definition: "Answer is concise, understandable, and appropriate for the audience.", score_1: "Difficult to follow or inappropriate detail.", score_3: "Mostly clear with some unnecessary detail.", score_5: "Clear structure, precise language, and audience-aware detail." },
];

const notes = [
  { topic: "Role scope", guidance: "The workbook contains exactly 657 roles, all defined by the existing MASCO role catalogue. ESCO, O*NET, NOC, and OSCA records enrich those roles; they do not create additional roles." },
  { topic: "Global interview content", guidance: "Each MASCO role receives 12 interview questions. Global occupation sources provide task, duty, requirement, and skill anchors. OPM and VA guidance informs structured interviewing and answer frameworks." },
  { topic: "Open Q&A", guidance: "The Open Q&A sheet contains licensed technical questions from 30 Seconds of Interviews and Continuum Analytics. Open QA Links recommends a small subset only where role-title keywords indicate technical relevance." },
  { topic: "Mapping quality", guidance: "ESCO mappings use the existing MASCO crosswalk. O*NET, NOC, and OSCA mappings use conservative English title similarity and always require human review before production." },
  { topic: "Source fidelity", guidance: "Interview Q&A rows are authored practice prompts, not verbatim employer questions. Open Q&A rows are retained from their source and marked separately." },
  { topic: "MASCO rights", guidance: "MASCO is the role backbone, but an explicit open-data licence for bulk redistribution was not confirmed in the supplied files. Confirm rights before external bulk release." },
  { topic: "Technical currentness", guidance: "The licensed technical Q&A repositories may contain outdated framework or vendor assumptions. Review versions and current practices before surfacing them." },
  { topic: "Fairness", guidance: "Use consistent job-relevant questions and rubrics for candidates in the same process. Do not ask about protected or personal characteristics. Provide reasonable accommodations and local legal review." },
  { topic: "Scoring", guidance: "Score evidence quality, ownership, method, outcome, reflection, and communication. Do not score accent, confidence style, school prestige, employment gaps, or cultural familiarity." },
  { topic: "Excluded collections", guidance: "Scraped Glassdoor, Indeed, Reddit, LeetCode, and unclear-licence Kaggle collections are not included. Public accessibility does not create reuse rights." },
];

const checksumBySource = {
  "MASCO-2020": [checksums[paths.mascoCrosswalk]],
  "ESCO-1.2.1": [checksums[paths.escoOccupations], checksums[paths.escoRelations]],
  "ONET-31.0": [checksums[paths.onetOccupations], checksums[paths.onetTasks], checksums[paths.onetEssential], checksums[paths.onetTransferable]],
  "NOC-2021-V1": [checksums[paths.nocRoles]],
  "OSCA-2024-V1": [checksums[paths.oscaRoles]],
  "GITHUB-30SECONDS-INTERVIEWS": [checksums[paths.secondsQuestions], checksums[paths.secondsLicense]],
  "GITHUB-CONTINUUM-INTERVIEW-QUESTIONS": [checksums[paths.continuumQuestions], checksums[paths.continuumLicense]],
  "OPM-STRUCTURED-INTERVIEWS": [],
  "VA-PBI": [checksums[paths.vaPage]],
};
for (const source of sources) {
  source.accessed_date = "2026-09-22";
  source.sha256 = (checksumBySource[source.source_id] ?? []).filter(Boolean).join("; ");
}

// Release raw source rows and large lookup maps before spreadsheet authoring.
for (const sourceRows of [mascoCrosswalk, escoOccupationsRaw, escoRelations, onetOccupations, onetTasks, onetEssential, onetTransferable, nocRoles, oscaRoles, secondsQuestions, continuumRecords]) sourceRows.length = 0;
escoOccupations.length = 0;
escoByCode.clear();
escoByTitle.clear();
escoSkillMap.clear();
onetTaskMap.clear();
onetSkillMap.clear();
mascoGroups.clear();

await fs.mkdir(outputDir, { recursive: true });
await fs.rm(previewDir, { recursive: true, force: true });
await fs.mkdir(previewDir, { recursive: true });

const workbook = Workbook.create();
const overview = workbook.worksheets.add("Overview");
const rolesSheet = workbook.worksheets.add("MASCO Roles");
const questionsSheet = workbook.worksheets.add("Interview Q&A");
const matchesSheet = workbook.worksheets.add("Global Matches");
const anchorsSheet = workbook.worksheets.add("Role Anchors");
const openQaSheet = workbook.worksheets.add("Open Q&A");
const openLinksSheet = workbook.worksheets.add("Open QA Links");
const coverageSheet = workbook.worksheets.add("Coverage");
const qualitySheet = workbook.worksheets.add("Data Quality");
const sourcesSheet = workbook.worksheets.add("Sources & Licences");
const rubricsSheet = workbook.worksheets.add("Rubrics");
const notesSheet = workbook.worksheets.add("Data Notes");

const colors = {
  navy: "#18324B",
  teal: "#087F8C",
  blueLight: "#E8F0F7",
  tealLight: "#DFF3F4",
  amber: "#FFF3CD",
  green: "#E2F0D9",
  red: "#FCE8E6",
  white: "#FFFFFF",
  grid: "#D4DEE8",
  text: "#1F2937",
  muted: "#5E6B78",
};
const font = "Arial";

function styleHeader(sheet, range) {
  const header = sheet.getRange(range);
  header.format = {
    fill: colors.navy,
    font: { name: font, size: 10, bold: true, color: colors.white },
    wrapText: true,
    verticalAlignment: "center",
    borders: { preset: "all", style: "thin", color: colors.white },
  };
  header.format.rowHeight = 34;
}

function setWidths(sheet, headers, widths) {
  for (const [header, width] of Object.entries(widths)) {
    const index = headers.indexOf(header);
    if (index >= 0) sheet.getRange(`${colLetter(index)}:${colLetter(index)}`).format.columnWidth = width;
  }
}

function writeSheet(sheet, rows, headers, { tableName = null, tableEndHeader = null, widths = {}, wrapColumns = [], rowHeight = 30, styleBody = true, chunkSize = 1000 } = {}) {
  const endCol = colLetter(headers.length - 1);
  sheet.getRange(`A1:${endCol}1`).values = [headers];
  for (let start = 0; start < rows.length; start += chunkSize) {
    const chunk = rows.slice(start, start + chunkSize).map((row) => headers.map((header) => row[header] ?? ""));
    const fromRow = start + 2;
    sheet.getRange(`A${fromRow}:${endCol}${fromRow + chunk.length - 1}`).values = chunk;
  }
  styleHeader(sheet, `A1:${endCol}1`);
  sheet.freezePanes.freezeRows(1);
  sheet.showGridLines = false;
  if (styleBody && rows.length) {
    sheet.getRange(`A2:${endCol}${rows.length + 1}`).format.font = { name: font, size: 9, color: colors.text };
    sheet.getRange(`A2:${endCol}${rows.length + 1}`).format.rowHeight = rowHeight;
    for (const column of wrapColumns) {
      const index = headers.indexOf(column);
      if (index >= 0) sheet.getRange(`${colLetter(index)}2:${colLetter(index)}${rows.length + 1}`).format.wrapText = true;
    }
  }
  setWidths(sheet, headers, widths);
  if (tableName && rows.length) {
    const lastIndex = tableEndHeader ? headers.indexOf(tableEndHeader) : headers.length - 1;
    const table = sheet.tables.add(`A1:${colLetter(lastIndex)}${rows.length + 1}`, true, tableName);
    table.style = "TableStyleMedium2";
    table.showFilterButton = true;
  }
  return { endRow: rows.length + 1, endCol };
}

const roleHeaders = [
  "role_id", "masco_code", "role_title", "locale", "role_standard", "crosswalk_status", "crosswalk_confidence", "mapped_masco2020_code",
  "mapped_masco2020_title", "global_sources", "global_match_count", "global_anchor_count", "question_count", "linked_open_qa_count",
  "role_source_url", "role_license_status",
];
const roleMeta = writeSheet(rolesSheet, roles, roleHeaders, {
  tableName: "MascoRolesTable",
  widths: { role_id: 15, masco_code: 14, role_title: 38, locale: 12, role_standard: 16, crosswalk_status: 18, crosswalk_confidence: 19, mapped_masco2020_code: 22, mapped_masco2020_title: 40, global_sources: 58, global_match_count: 18, global_anchor_count: 19, question_count: 16, linked_open_qa_count: 21, role_source_url: 70, role_license_status: 62 },
  wrapColumns: ["mapped_masco2020_title", "global_sources", "role_license_status"],
  rowHeight: 52,
});
rolesSheet.getRange("K2").formulas = [[`=COUNTIF('Global Matches'!$B$2:$B$${matches.length + 1},A2)`]];
rolesSheet.getRange(`K2:K${roleMeta.endRow}`).fillDown();
rolesSheet.getRange("L2").formulas = [[`=COUNTIF('Role Anchors'!$B$2:$B$${roleAnchors.length + 1},A2)`]];
rolesSheet.getRange(`L2:L${roleMeta.endRow}`).fillDown();
rolesSheet.getRange("M2").formulas = [[`=COUNTIF('Interview Q&A'!$B$2:$B$${questions.length + 1},A2)`]];
rolesSheet.getRange(`M2:M${roleMeta.endRow}`).fillDown();
rolesSheet.getRange("N2").formulas = [[`=COUNTIF('Open QA Links'!$B$2:$B$${Math.max(openQaLinks.length + 1, 2)},A2)`]];
rolesSheet.getRange(`N2:N${roleMeta.endRow}`).fillDown();

const questionHeaders = [
  "question_id", "role_id", "masco_code", "role_title", "locale", "category", "difficulty", "question_text", "anchor_type", "anchor_text",
  "global_anchor_standard", "global_anchor_record_id", "global_anchor_url", "global_anchor_license_id", "interview_method_sources", "authoring_method",
  "answer_framework", "answer_guidance", "strong_evidence_signals", "watch_out_for", "follow_up_question", "quality_score_100", "review_status", "safety_note",
];
const questionMeta = writeSheet(questionsSheet, questions, questionHeaders, {
  tableName: "InterviewQAIndex",
  tableEndHeader: "global_anchor_standard",
  widths: { question_id: 22, role_id: 15, masco_code: 14, role_title: 36, locale: 12, category: 20, difficulty: 14, question_text: 72, anchor_type: 17, anchor_text: 62, global_anchor_standard: 34, global_anchor_record_id: 58, global_anchor_url: 68, global_anchor_license_id: 34, interview_method_sources: 35, authoring_method: 52, answer_framework: 29, answer_guidance: 64, strong_evidence_signals: 60, watch_out_for: 58, follow_up_question: 52, quality_score_100: 18, review_status: 44, safety_note: 68 },
  styleBody: false,
});

const matchHeaders = ["match_id", "role_id", "masco_code", "masco_title", "global_source_standard", "global_source_code", "global_source_title", "mapping_method", "title_similarity_0_100", "mapping_confidence", "source_record_id", "source_url", "license_id", "source_description", "review_status"];
const matchMeta = writeSheet(matchesSheet, matches, matchHeaders, {
  tableName: "GlobalMatchesTable",
  widths: { match_id: 20, role_id: 15, masco_code: 14, masco_title: 36, global_source_standard: 34, global_source_code: 20, global_source_title: 38, mapping_method: 24, title_similarity_0_100: 22, mapping_confidence: 19, source_record_id: 58, source_url: 68, license_id: 34, source_description: 72, review_status: 42 },
  wrapColumns: ["source_description", "review_status"],
  rowHeight: 52,
});
matchesSheet.getRange(`I2:I${matchMeta.endRow}`).format.numberFormat = "0";

const anchorHeaders = ["anchor_id", "role_id", "masco_code", "role_title", "anchor_rank", "anchor_type", "anchor_text", "source_standard", "source_record_id", "source_url", "license_id"];
const anchorMeta = writeSheet(anchorsSheet, roleAnchors, anchorHeaders, {
  tableName: "RoleAnchorsTable",
  widths: { anchor_id: 20, role_id: 15, masco_code: 14, role_title: 36, anchor_rank: 13, anchor_type: 16, anchor_text: 70, source_standard: 34, source_record_id: 60, source_url: 68, license_id: 34 },
  wrapColumns: ["anchor_text"],
  rowHeight: 48,
  styleBody: false,
});

const openQaHeaders = ["qa_id", "source_id", "source_record_id", "topic_or_section", "expertise", "question_text", "source_answer", "good_to_hear", "answer_status", "active_for_practice", "currentness_status", "license_id", "source_url", "attribution", "review_note"];
const openQaMeta = writeSheet(openQaSheet, openQa, openQaHeaders, {
  tableName: "OpenQATable",
  widths: { qa_id: 19, source_id: 38, source_record_id: 34, topic_or_section: 34, expertise: 16, question_text: 66, source_answer: 85, good_to_hear: 62, answer_status: 23, active_for_practice: 30, currentness_status: 38, license_id: 34, source_url: 70, attribution: 58, review_note: 65 },
  wrapColumns: ["question_text", "source_answer", "good_to_hear", "attribution", "review_note"],
  rowHeight: 82,
});
openQaSheet.getRange(`J2:J${openQaMeta.endRow}`).conditionalFormats.add("containsText", { text: "no", format: { fill: colors.red, font: { color: "#9C0006", bold: true } } });

const openLinkHeaders = ["link_id", "role_id", "masco_code", "role_title", "qa_id", "qa_source_id", "qa_topic", "question_text", "relevance_rule", "license_id", "source_url", "review_status"];
const openLinkMeta = writeSheet(openLinksSheet, openQaLinks, openLinkHeaders, {
  tableName: "OpenQALinksTable",
  widths: { link_id: 20, role_id: 15, masco_code: 14, role_title: 36, qa_id: 20, qa_source_id: 40, qa_topic: 35, question_text: 72, relevance_rule: 66, license_id: 34, source_url: 70, review_status: 44 },
  wrapColumns: ["question_text", "relevance_rule"],
  rowHeight: 60,
});

const coverageHeaders = ["role_id", "masco_code", "role_title", "expected_questions", "actual_questions", "expected_global_matches_minimum", "actual_global_matches", "actual_global_anchors", "linked_open_qa_records", "qa_status"];
const coverageMeta = writeSheet(coverageSheet, coverageRows, coverageHeaders, {
  tableName: "CoverageTable",
  widths: { role_id: 15, masco_code: 14, role_title: 38, expected_questions: 20, actual_questions: 18, expected_global_matches_minimum: 31, actual_global_matches: 22, actual_global_anchors: 22, linked_open_qa_records: 23, qa_status: 14 },
  rowHeight: 31,
});
coverageSheet.getRange("E2").formulas = [[`=COUNTIF('Interview Q&A'!$B$2:$B$${questionMeta.endRow},A2)`]];
coverageSheet.getRange(`E2:E${coverageMeta.endRow}`).fillDown();
coverageSheet.getRange("G2").formulas = [[`=COUNTIF('Global Matches'!$B$2:$B$${matchMeta.endRow},A2)`]];
coverageSheet.getRange(`G2:G${coverageMeta.endRow}`).fillDown();
coverageSheet.getRange("H2").formulas = [[`=COUNTIF('Role Anchors'!$B$2:$B$${anchorMeta.endRow},A2)`]];
coverageSheet.getRange(`H2:H${coverageMeta.endRow}`).fillDown();
coverageSheet.getRange("I2").formulas = [[`=COUNTIF('Open QA Links'!$B$2:$B$${Math.max(openLinkMeta.endRow, 2)},A2)`]];
coverageSheet.getRange(`I2:I${coverageMeta.endRow}`).fillDown();
coverageSheet.getRange("J2").formulas = [["=IF(AND(D2=E2,G2>=F2,H2>=1),\"PASS\",\"REVIEW\")"]];
coverageSheet.getRange(`J2:J${coverageMeta.endRow}`).fillDown();
coverageSheet.getRange(`J2:J${coverageMeta.endRow}`).conditionalFormats.add("containsText", { text: "PASS", format: { fill: colors.green, font: { color: "#006100", bold: true } } });
coverageSheet.getRange(`J2:J${coverageMeta.endRow}`).conditionalFormats.add("containsText", { text: "REVIEW", format: { fill: colors.red, font: { color: "#9C0006", bold: true } } });

const qualityHeaders = ["check_id", "check", "expected", "actual", "status", "evidence"];
const qualityMeta = writeSheet(qualitySheet, qualityChecks, qualityHeaders, {
  tableName: "DataQualityTable",
  widths: { check_id: 12, check: 54, expected: 18, actual: 18, status: 14, evidence: 72 },
  wrapColumns: ["check", "evidence"],
  rowHeight: 47,
});
qualitySheet.getRange(`E2:E${qualityMeta.endRow}`).conditionalFormats.add("containsText", { text: "PASS", format: { fill: colors.green, font: { color: "#006100", bold: true } } });
qualitySheet.getRange(`E2:E${qualityMeta.endRow}`).conditionalFormats.add("containsText", { text: "FAIL", format: { fill: colors.red, font: { color: "#9C0006", bold: true } } });

const sourceHeaders = ["source_id", "name", "publisher", "version", "source_use", "source_url", "licence", "licence_url", "production_eligibility", "attribution_or_obligation", "quality_note", "accessed_date", "sha256"];
const sourceMeta = writeSheet(sourcesSheet, sources, sourceHeaders, {
  tableName: "SourcesLicencesTable",
  widths: { source_id: 38, name: 50, publisher: 55, version: 43, source_use: 60, source_url: 72, licence: 62, licence_url: 72, production_eligibility: 55, attribution_or_obligation: 72, quality_note: 68, accessed_date: 17, sha256: 88 },
  wrapColumns: ["publisher", "source_use", "licence", "production_eligibility", "attribution_or_obligation", "quality_note"],
  rowHeight: 78,
});

const rubricHeaders = ["dimension", "definition", "score_1", "score_3", "score_5"];
const rubricMeta = writeSheet(rubricsSheet, rubricRows, rubricHeaders, {
  tableName: "RubricsTable",
  widths: { dimension: 20, definition: 52, score_1: 48, score_3: 52, score_5: 58 },
  wrapColumns: ["definition", "score_1", "score_3", "score_5"],
  rowHeight: 68,
});

const noteHeaders = ["topic", "guidance"];
const noteMeta = writeSheet(notesSheet, notes, noteHeaders, {
  tableName: "DataNotesTable",
  widths: { topic: 29, guidance: 120 },
  wrapColumns: ["guidance"],
  rowHeight: 62,
});

overview.showGridLines = false;
overview.getRange("A1").values = [["MASCO 657 interview assistant dataset"]];
overview.getRange("A1").format = { font: { name: font, size: 18, bold: true, color: colors.navy } };
overview.getRange("A2").values = [["Global occupation sources and open interview Q&A enrich the existing MASCO role catalogue; no roles are added."]];
overview.getRange("A2").format = { font: { name: font, size: 10, italic: true, color: colors.muted } };
overview.getRange("A3:L3").format.fill = colors.navy;
overview.getRange("A3:L3").format.rowHeight = 3;

overview.getRange("A5:B12").values = [
  ["Dataset metric", "Value"],
  ["MASCO roles", ""],
  ["Interview questions", ""],
  ["Global match records", ""],
  ["Global anchor records", ""],
  ["Open Q&A records", ""],
  ["Open Q&A role links", ""],
  ["Quality checks passed", ""],
];
overview.getRange("B6").formulas = [[`=COUNTA('MASCO Roles'!$A$2:$A$${roleMeta.endRow})`]];
overview.getRange("B7").formulas = [[`=COUNTA('Interview Q&A'!$A$2:$A$${questionMeta.endRow})`]];
overview.getRange("B8").formulas = [[`=COUNTA('Global Matches'!$A$2:$A$${matchMeta.endRow})`]];
overview.getRange("B9").formulas = [[`=COUNTA('Role Anchors'!$A$2:$A$${anchorMeta.endRow})`]];
overview.getRange("B10").formulas = [[`=COUNTA('Open Q&A'!$A$2:$A$${openQaMeta.endRow})`]];
overview.getRange("B11").formulas = [[`=COUNTA('Open QA Links'!$A$2:$A$${openLinkMeta.endRow})`]];
overview.getRange("B12").formulas = [[`=COUNTIF('Data Quality'!$E$2:$E$${qualityMeta.endRow},"PASS")`]];
styleHeader(overview, "A5:B5");
overview.getRange("A6:A12").format = { fill: colors.blueLight, font: { name: font, size: 10, bold: true, color: colors.text } };
overview.getRange("B6:B12").format = { font: { name: font, size: 13, bold: true, color: colors.teal }, numberFormat: "#,##0" };

overview.getRange("D5:I10").values = [
  ["Global source", "Matched MASCO roles", "Match records", "Anchor records", "Mapping method", "Review requirement"],
  ...sourceCoverage.map((row) => [row.global_source_standard, row.matched_masco_roles, row.match_records, row.anchor_records, row.mapping_method, row.review_requirement]),
  ["Open technical Q&A", new Set(openQaLinks.map((link) => link.role_id)).size, openQaLinks.length, openQa.length, "Role-title keyword to Q&A topic", "Human relevance and currentness review required"],
];
styleHeader(overview, "D5:I5");
overview.getRange("D6:I10").format.font = { name: font, size: 9, color: colors.text };
overview.getRange("D6:I10").format.rowHeight = 42;
overview.getRange("H6:I10").format.wrapText = true;
overview.getRange("D:D").format.columnWidth = 35;
overview.getRange("E:G").format.columnWidth = 20;
overview.getRange("H:H").format.columnWidth = 35;
overview.getRange("I:I").format.columnWidth = 47;

overview.getRange("A14").values = [["Role boundary"]];
overview.getRange("A14:L14").format = { fill: colors.teal, font: { name: font, size: 11, bold: true, color: colors.white } };
overview.getRange("A15:L17").merge();
overview.getRange("A15").values = [["The workbook contains exactly 657 MASCO roles. ESCO, O*NET, NOC, and OSCA are used only to enrich those roles with global tasks, duties, requirements, and skills. The Interview Q&A sheet contains 12 authored practice questions per MASCO role. The Open Q&A sheet remains a separate licensed technical corpus."]];
overview.getRange("A15:L17").format = { fill: colors.tealLight, font: { name: font, size: 10, color: colors.text }, wrapText: true, verticalAlignment: "top" };

overview.getRange("A19").values = [["Use and limitations"]];
overview.getRange("A19:L19").format = { fill: "#B45F06", font: { name: font, size: 11, bold: true, color: colors.white } };
overview.getRange("A20:L23").merge();
overview.getRange("A20").values = [["Filter MASCO Roles to choose the target role, then use role_id in Interview Q&A. Review Global Matches and Role Anchors before publishing a role pack. Title-similarity mappings and technical Q&A links require human review. Confirm MASCO redistribution rights, preserve all source licences, and complete domain, fairness, and local legal review before production use."]];
overview.getRange("A20:L23").format = { fill: colors.amber, font: { name: font, size: 10, color: colors.text }, wrapText: true, verticalAlignment: "top" };

overview.getRange("A:A").format.columnWidth = 29;
overview.getRange("B:B").format.columnWidth = 16;
overview.getRange("C:C").format.columnWidth = 4;
overview.getRange("J:L").format.columnWidth = 12;
overview.getRange("1:2").format.rowHeight = 25;
overview.getRange("15:17").format.rowHeight = 25;
overview.getRange("20:23").format.rowHeight = 25;

const chart = overview.charts.add("bar", overview.getRange("D5:E9"));
chart.title = "MASCO roles with a global source match";
chart.titleTextStyle.typeface = font;
chart.hasLegend = false;
chart.xAxis = { numberFormatCode: "#,##0", numberFormatSourceLinked: false, textStyle: { typeface: font } };
chart.yAxis = { textStyle: { typeface: font } };
chart.setPosition("J5", "L13");

const overviewInspection = await workbook.inspect({ kind: "region", sheetId: "Overview", range: "A1:L23", maxChars: 6500, tableMaxRows: 30, tableMaxCols: 12 });
console.log("OVERVIEW_INSPECTION");
console.log(overviewInspection.ndjson ?? overviewInspection);

const questionInspection = await workbook.inspect({ kind: "table", range: "Interview Q&A!A1:X9", include: "values,formulas", tableMaxRows: 9, tableMaxCols: 24, maxChars: 12000 });
console.log("QUESTION_SAMPLE");
console.log(questionInspection.ndjson ?? questionInspection);

const coverageInspection = await workbook.inspect({ kind: "formula", sheetId: "Coverage", range: `A1:J${Math.min(coverageMeta.endRow, 12)}`, options: { maxResults: 100 }, maxChars: 6000 });
console.log("COVERAGE_FORMULAS");
console.log(coverageInspection.ndjson ?? coverageInspection);

const errorInspection = await workbook.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!", options: { useRegex: true, maxResults: 300 }, summary: "final formula error scan", maxChars: 6000 });
console.log("FORMULA_ERROR_SCAN");
console.log(errorInspection.ndjson ?? errorInspection);

const previewSpecs = [
  ["Overview", "A1:L23"],
  ["MASCO Roles", "A1:P10"],
  ["Interview Q&A", "A1:X9"],
  ["Global Matches", "A1:O10"],
  ["Role Anchors", "A1:K10"],
  ["Open Q&A", "A1:O8"],
  ["Open QA Links", "A1:L9"],
  ["Coverage", "A1:J10"],
  ["Data Quality", `A1:F${qualityMeta.endRow}`],
  ["Sources & Licences", `A1:M${sourceMeta.endRow}`],
  ["Rubrics", `A1:E${rubricMeta.endRow}`],
  ["Data Notes", `A1:B${noteMeta.endRow}`],
];
console.log("Rendering previews");
for (const [sheetName, range] of previewSpecs) {
  const preview = await workbook.render({ sheetName, range, scale: 1, format: "png" });
  await fs.writeFile(path.join(previewDir, `${sheetName.toLowerCase().replace(/[^a-z0-9]+/g, "_")}.png`), new Uint8Array(await preview.arrayBuffer()));
}

console.log("Exporting workbook");
const xlsx = await SpreadsheetFile.exportXlsx(workbook);
await xlsx.save(outputPath);
await fs.rm(`${outputPath}.inspect.ndjson`, { force: true });

console.log(JSON.stringify({
  outputPath,
  previewDir,
  counts: {
    mascoRoles: roles.length,
    interviewQuestions: roleQuestionCount,
    globalMatches: matches.length,
    globalAnchors: roleAnchors.length,
    openQa: openQa.length,
    openQaLinks: openQaLinks.length,
    qualityChecksPassed: qualityChecks.filter((check) => check.status === "PASS").length,
    qualityChecksFailed: qualityChecks.filter((check) => check.status === "FAIL").length,
  },
  rolesBySourceMatch: Object.fromEntries(sourceCoverage.map((row) => [row.global_source_standard, row.matched_masco_roles])),
  failedChecks: qualityChecks.filter((check) => check.status === "FAIL"),
}, null, 2));
