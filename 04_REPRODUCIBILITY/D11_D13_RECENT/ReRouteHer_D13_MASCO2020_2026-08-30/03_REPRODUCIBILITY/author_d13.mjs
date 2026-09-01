// CSV authoring and a review workbook, using only the supported artifact API.
import fs from 'node:fs/promises';
import path from 'node:path';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';
const root=process.argv[2];if(!root)throw new Error('Pass the absolute release directory');
const payload=JSON.parse(await fs.readFile(path.join(root,'02_QA/table_payloads.json'),'utf8'));
const summary=JSON.parse(await fs.readFile(path.join(root,'02_QA/D13_build_summary.json'),'utf8'));
const tests=JSON.parse(await fs.readFile(path.join(root,'02_QA/title_case_tests.json'),'utf8')).cases;
const quote=v=>'"'+String(v??'').replaceAll('"','""')+'"';
const line=r=>r.map(quote).join(',')+'\r\n';
const escape=v=>typeof v==='string'&&(/^\d{4}-\d\d-\d\dT/.test(v)||v.startsWith('='));
const safe=v=>escape(v)?"'"+v:v;
const letter=n=>{let s='';for(n++;n>0;n=Math.floor((n-1)/26))s=String.fromCharCode(65+(n-1)%26)+s;return s;};
function write(sh,columns,rows,start=0){
 sh.getRangeByIndexes(start,0,1,columns.length).values=[columns];
 for(let k=0;k<columns.length;k++)if(typeof rows[0]?.[k]==='string')sh.getRangeByIndexes(start+1,k,rows.length,1).setNumberFormat('@');
 for(let i=0;i<rows.length;i+=1500){let b=rows.slice(i,i+1500);sh.getRangeByIndexes(start+i+1,0,b.length,columns.length).values=b.map(r=>r.map(safe));}
}
const checks=[];
if(!process.argv.includes('--workbook-only'))for(const [rel,{columns,rows}] of Object.entries(payload)){
 const wb=Workbook.create(),sh=wb.worksheets.add('Data');write(sh,columns,rows);
 const chunks=[line(columns)];
 for(let i=0;i<rows.length;i+=1500){
  const original=rows.slice(i,i+1500),actual=sh.getRangeByIndexes(i+1,0,original.length,columns.length).values;
  for(let j=0;j<original.length;j++)for(let k=0;k<columns.length;k++){
   if(escape(original[j][k])&&actual[j][k]==="'"+original[j][k])actual[j][k]=actual[j][k].slice(1);
   if(String(original[j][k]??'')!==String(actual[j][k]??''))throw new Error(`Round-trip mismatch ${rel}:${i+j}:${columns[k]}`);
  }
  chunks.push(...actual.map(line));
 }
 await fs.writeFile(path.join(root,rel),chunks.join(''),'utf8');
 checks.push({file:rel,rows:rows.length,columns:columns.length,round_trip:'PASS'});console.log(JSON.stringify(checks.at(-1)));
}
if(checks.length)await fs.writeFile(path.join(root,'02_QA/artifact_authoring_checks.json'),JSON.stringify(checks,null,2)+'\n');
function records(rel){const t=payload[rel];return t.rows.map(r=>Object.fromEntries(t.columns.map((c,i)=>[c,r[i]])));}
const wb=Workbook.create(),sh=wb.worksheets.add('Summary');
const sheets=[];
function reviewSheet(name,title,note,cols,rows,widths,height=64){
 const ws=wb.worksheets.add(name);write(ws,cols,rows,3);ws.showGridLines=false;ws.freezePanes.freezeRows(4);
 const used=ws.getRangeByIndexes(0,0,rows.length+4,cols.length);used.format.font={name:'Aptos',size:11,color:'#24383D'};used.format.wrapText=true;used.format.rowHeightPx=height;
 for(let i=0;i<cols.length;i++)ws.getRangeByIndexes(0,i,rows.length+4,1).format.columnWidthPx=widths[i]??220;
 const end=letter(Math.min(cols.length,6)-1);
 ws.getRange(`A1:${end}1`).merge();ws.getRange('A1').values=[[title]];ws.getRange(`A1:${end}1`).format.fill='#164B55';ws.getRange('A1').format.font={bold:true,size:19,color:'#FFFFFF'};ws.getRange(`A1:${end}1`).format.rowHeightPx=48;
 ws.getRange(`A2:${end}2`).merge();ws.getRange('A2').values=[[note]];ws.getRange(`A2:${end}2`).format.fill='#E9F2F1';ws.getRange(`A2:${end}2`).format.rowHeightPx=58;
 ws.getRange(`A3:${letter(cols.length-1)}3`).format.rowHeightPx=14;
 const tab=ws.tables.add(`A4:${letter(cols.length-1)}${rows.length+4}`,true,name.replaceAll(' ','')+'Data');tab.style='TableStyleMedium2';
 ws.getRangeByIndexes(3,0,1,cols.length).format.fill='#164B55';ws.getRangeByIndexes(3,0,1,cols.length).format.font={bold:true,color:'#FFFFFF'};ws.getRangeByIndexes(3,0,1,cols.length).format.rowHeightPx=42;
 sheets.push({name,rows:rows.length,columns:cols.length});return ws;
}
const cov=records('01_TABLES/D13_role_esco_coverage.csv');
reviewSheet('Mappings','D13 | MASCO 2020 → ESCO','655 six-digit role identities. ESCO titles use Title Case; codes are unchanged text identifiers. Broader/partial mappings remain test proxies.',
 ['Role ID','MASCO Code','MASCO 2020 Role','ESCO Code','ESCO Occupation Title','Relation','Confidence','MASCO Source','ESCO Source'],
 cov.map(r=>[r.role_id,r.masco_code,r.role_title,r.chosen_esco_code,r.chosen_esco_title,r.mapping_relation,r.mapping_confidence,r.masco_source_url,r.esco_source_url]),
 [110,100,350,120,330,150,110,420,420],72);
const skills=records('01_TABLES/skill_taxonomy.csv'),sl=new Map(records('01_TABLES/skill_taxonomy_lineage.csv').map(r=>[r.skill_id,r]));
reviewSheet('Skills','D13 | Concrete ESCO Skill Vocabulary','All linked skills, with Title Case display names. Definitions retain original sentence case; raw labels and source categories remain in lineage.',
 ['Skill ID','Canonical Name','Skill Type','Definition','Raw ESCO Label','ESCO Source'],
 skills.map(r=>[r.skill_id,r.canonical_name,r.skill_type,r.definition,sl.get(r.skill_id).preferred_label_raw,sl.get(r.skill_id).concept_uri]),
 [320,340,110,660,340,420],110);
const alias=records('01_TABLES/skill_aliases_lineage.csv');
reviewSheet('Aliases','D13 | Matching Aliases','Matching aliases are intentionally lowercase. Display labels use Title Case; SQL, ICT and product spellings are preserved in display text.',
 ['Skill ID','Lowercase Match Alias','Title Case Display Alias','Source Types','ESCO Source'],
 alias.map(r=>[r.skill_id,r.alias,r.alias_display_title,r.all_alias_sources,r.source_url]),[320,380,380,220,420],58);
const changed=records('02_QA/D13_mapping_changes.csv').filter(r=>r.esco_code_changed);
reviewSheet('Changes','D13 | Changed Primary ESCO Assignments','Only changed occupation codes are listed here. The complete 655-row comparison audit is included in the CSV package.',
 ['MASCO Code','MASCO 2020 Role','Previous ESCO Code','Previous ESCO Title','New ESCO Code','New ESCO Title','Reason'],
 changed.map(r=>[r.masco_code,r.role_title,r.previous_esco_code,r.previous_esco_title,r.chosen_esco_code,r.chosen_esco_title,r.rationale]),[110,360,140,340,140,340,650],88);
reviewSheet('Case Rules','D13 | Title Case Regression Tests','Capitalize principal words; keep interior articles, conjunctions and prepositions lowercase. Protect technical spellings without turning “visual aids” into “visual AIDS.”',
 ['Input Label','Expected Display','Actual Display','Passed'],tests.map(r=>[r.input,r.expected,r.actual,r.passed?'PASS':'FAIL']),[380,380,380,100],46);
const comp=records('01_TABLES/ESCO_comparison_preservation.csv');
reviewSheet('ESCO Comparison','D13 | Original ESCO Comparison Preserved','All 657 original current-portal source records remain in the audit, including the 19 excluded from active MASCO 2020 scope. Codes are unchanged; display titles are recased.',
 ['Source Role ID','Source MASCO Code','Source Role Title','2020 Scope Status','2020 Role IDs','Previous D13 ESCO Code','Previous D13 ESCO Title','D11 Comparison Codes','D11 Comparison Titles'],
 comp.map(r=>[r.source_current_role_id,r.source_current_masco_code,r.source_current_role_title,r.status,r.masco2020_role_ids,r.d13_esco_code,r.d13_esco_title,r.d11_esco_comparison_codes,r.d11_esco_comparison_titles]),[140,130,350,240,220,170,340,240,520],82);
sh.showGridLines=false;sh.getRange('A1:E24').format.font={name:'Aptos',size:12,color:'#24383D'};sh.getRange('A1:E24').format.wrapText=true;sh.getRange('A1:E24').format.rowHeightPx=42;
for(const [col,width] of [['A',330],['B',110],['C',170],['D',170],['E',170]])sh.getRange(`${col}1:${col}24`).format.columnWidthPx=width;
sh.getRange('A1:E1').merge();sh.getRange('A1').values=[['ReRouteHer | D13 Rebuilt on MASCO 2020']];sh.getRange('A1:E1').format.fill='#164B55';sh.getRange('A1').format.font={size:21,bold:true,color:'#FFFFFF'};sh.getRange('A1:E1').format.rowHeightPx=58;
sh.getRange('A2:E2').merge();sh.getRange('A2').values=[['30 August 2026 • ESCO v1.2.1 • Consistent Title Case • Test-only mappings']];
sh.getRange('A4:B4').values=[['Coverage and Checks','Count']];sh.getRange('C4:E4').merge();sh.getRange('C4').values=[['Interpretation']];sh.getRange('A4:E4').format.fill='#164B55';sh.getRange('A4:E4').format.font={bold:true,color:'#FFFFFF'};
const metrics=[
 ['MASCO 2020 roles',`=COUNTA('Mappings'!A5:A${cov.length+4})`,'Six-digit role codes, with one primary ESCO occupation each.'],
 ['Concrete ESCO skills',`=COUNTA('Skills'!A5:A${skills.length+4})`,'Only skills linked to the selected occupations.'],
 ['Lowercase matching aliases',`=COUNTA('Aliases'!A5:A${alias.length+4})`,'Separate from Title Case display labels.'],
 ['Changed ESCO assignments',`=COUNTA('Changes'!A5:A${changed.length+4})`,'Updated using the 2020 titles and reviewed duties.'],
 ['Close functional matches',`=COUNTIF('Mappings'!F5:F${cov.length+4},"close_match")`,'Not a certification or licensing equivalence.'],
 ['Broader proxies',`=COUNTIF('Mappings'!F5:F${cov.length+4},"broader_proxy")`,'The ESCO scope is broader than the selected role.'],
 ['Partial proxies',`=COUNTIF('Mappings'!F5:F${cov.length+4},"partial_proxy")`,'Only part of the scope is represented.'],
 ['Original ESCO comparisons',`=COUNTA('ESCO Comparison'!A5:A${comp.length+4})`,'Includes original source records excluded from active scope.'],
 ['Title Case regression tests',`=COUNTIF('Case Rules'!D5:D${tests.length+4},"PASS")`,'Includes acronyms, products, possessives and ambiguous words.'],
];
for(let i=0;i<metrics.length;i++){const r=i+5;sh.getRange(`A${r}`).values=[[metrics[i][0]]];sh.getRange(`B${r}`).formulas=[[metrics[i][1]]];sh.getRange(`C${r}:E${r}`).merge();sh.getRange(`C${r}`).values=[[metrics[i][2]]];}
sh.getRange('B5:B13').setNumberFormat('#,##0');sh.getRange('B5:B13').format.font={size:17,bold:true,color:'#164B55'};
sh.getRange('A15:E15').merge();sh.getRange('A15').values=[['Read Before Importing']];sh.getRange('A15:E15').format.fill='#164B55';sh.getRange('A15').format.font={bold:true,color:'#FFFFFF'};
for(const [r,note] of [
 [16,`The full package contains ${summary.role_skill_rows.toLocaleString('en-US')} role–skill links (essential = 100, optional = 50), regenerated 384-dimensional skill vectors, provenance and case audits.`],
 [18,'Raw ESCO source CSVs are unchanged. Human-readable ESCO display fields use Title Case. Definitions, identifiers, URLs, enums and lowercase matching aliases are deliberately exempt.'],
 [20,'No live database, schema, remote-work rating or deployed model was changed. The guarded SQL is for a separate empty test database; do not append over an existing taxonomy version.'],
 [22,'Sources: MASCO 2020 STEM release (655 roles); official ESCO classification v1.2.1. Source URLs are attached to rows. https://esco.ec.europa.eu/en/use-esco/download'],
 [24,'All mappings remain project test proxies. Expert validation of occupational scope and Malaysian qualification requirements is still required before production.'],
]){sh.getRange(`A${r}:E${r}`).merge();sh.getRange(`A${r}`).values=[[note]];sh.getRange(`A${r}:E${r}`).format.rowHeightPx=70;}
const counts=sh.getRange('B5:B13').values.flat();const expected=[655,summary.scoped_leaf_skills,summary.skill_alias_rows,summary.changed_primary_esco_codes,summary.mapping_relation_counts.close_match,summary.mapping_relation_counts.broader_proxy,summary.mapping_relation_counts.partial_proxy,657,tests.length];
if(JSON.stringify(counts)!==JSON.stringify(expected))throw new Error('Summary mismatch '+JSON.stringify(counts));
const scan=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A',options:{useRegex:true,maxResults:15},maxChars:1500});
await fs.writeFile(path.join(root,'02_QA/workbook_checks.json'),JSON.stringify({counts,expected,scan:scan.ndjson,sheets},null,2)+'\n');
const preview=path.join(root,'02_QA/previews');await fs.mkdir(preview,{recursive:true});
for(const [name,range] of [['Summary','A1:E24'],['Mappings','A1:F8'],['Skills','A1:F8'],['Aliases','A1:E8'],['Changes','A1:F8'],['Case Rules','A1:D12'],['ESCO Comparison','A1:G8']]){
 const img=await wb.render({sheetName:name,range,scale:1.2,format:'png'});await fs.writeFile(path.join(preview,name.replaceAll(' ','_')+'.png'),new Uint8Array(await img.arrayBuffer()));
}
const outputDir=path.join(path.dirname(root),'outputs/01a047e7-ceba-7df3-8d1a-ba8071e66430');await fs.mkdir(outputDir,{recursive:true});
const output=await SpreadsheetFile.exportXlsx(wb);await output.save(path.join(outputDir,'D13_MASCO2020_TitleCase_Review.xlsx'));
console.log(JSON.stringify({workbook:path.join(outputDir,'D13_MASCO2020_TitleCase_Review.xlsx'),counts}));
