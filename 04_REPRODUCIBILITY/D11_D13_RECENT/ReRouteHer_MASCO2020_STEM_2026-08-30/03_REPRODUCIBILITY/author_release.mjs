// Author final CSV matrices and a compact review workbook with artifact-tool.
import fs from 'node:fs/promises';
import path from 'node:path';
import {Workbook, SpreadsheetFile} from '@oai/artifact-tool';

const root=process.argv[2];
if(!root)throw new Error('Pass the absolute release directory');
const payload=JSON.parse(await fs.readFile(path.join(root,'02_QA/table_payloads.json'),'utf8'));
const qa=[], previews=path.join(root,'02_QA/previews');
await fs.mkdir(previews,{recursive:true});
const csvLine=row=>row.map(v=>'"'+String(v??'').replaceAll('"','""')+'"').join(',')+'\r\n';
const escapeText=v=>typeof v==='string' && (/^\d{4}-\d\d-\d\dT/.test(v)||v.startsWith('='));
const safe=v=>escapeText(v)?"'"+v:v;
const letter=n=>{let out='';for(n++;n>0;n=Math.floor((n-1)/26))out=String.fromCharCode(65+(n-1)%26)+out;return out;};
function matrix(sh,columns,rows,start=0){
  sh.getRangeByIndexes(start,0,1,columns.length).values=[columns];
  for(let k=0;k<columns.length;k++)if(typeof rows[0]?.[k]==='string')
    sh.getRangeByIndexes(start+1,k,rows.length,1).setNumberFormat('@');
  for(let i=0;i<rows.length;i+=1500){const block=rows.slice(i,i+1500);
    sh.getRangeByIndexes(start+i+1,0,block.length,columns.length).values=block.map(row=>row.map(safe));}
}
for(const [rel,{columns,rows}] of (process.argv.includes('--workbook-only')?[]:Object.entries(payload))){
  const wb=Workbook.create(), sh=wb.worksheets.add('Data');matrix(sh,columns,rows);
  const chunks=[csvLine(columns)];
  for(let i=0;i<rows.length;i+=1500){
    const original=rows.slice(i,i+1500),actual=sh.getRangeByIndexes(i+1,0,original.length,columns.length).values;
    for(let j=0;j<original.length;j++)for(let k=0;k<columns.length;k++){
      if(escapeText(original[j][k])&&actual[j][k]==="'"+original[j][k])actual[j][k]=actual[j][k].slice(1);
      if(String(actual[j][k]??'')!==String(original[j][k]??''))throw new Error(`Round-trip mismatch ${rel}:${i+j}:${columns[k]}`);
    }
    chunks.push(...actual.map(csvLine));
  }
  await fs.writeFile(path.join(root,rel),chunks.join(''),'utf8');
  qa.push({file:rel,rows:rows.length,columns:columns.length,round_trip:'PASS'});
  console.log(JSON.stringify(qa.at(-1)));
}
if(qa.length)await fs.writeFile(path.join(root,'02_QA/artifact_authoring_checks.json'),JSON.stringify(qa,null,2)+'\n');

// The machine tables retain their source headers. This workbook is a readable
// review companion; all summary counts are formulas over visible audit sheets.
const wb=Workbook.create(), overview=wb.worksheets.add('Summary');
const specs=[
  ['Retained','01_TABLES/MASCO2020_retained_roles.csv',[120,110,370,160,320,180,370,240,130,140,450]],
  ['Excluded','01_TABLES/MASCO2020_excluded_roles.csv',[150,130,380,150,130,370,110,260,140,560]],
  ['Crosswalk','01_TABLES/MASCO2020_role_crosswalk.csv',[150,130,380,150,130,370,110,260,140,560]],
  ['ESCO comparison','01_TABLES/ESCO_comparison_preservation.csv',[150,130,380,180,220,130,350,140,280,420,150,180,180]],
];
for(const [name,rel,widths] of specs){
  const sh=wb.worksheets.add(name),{columns,rows}=payload[rel];
  matrix(sh,columns,rows,4);sh.showGridLines=false;sh.freezePanes.freezeRows(5);
  const used=sh.getRangeByIndexes(0,0,rows.length+5,columns.length);
  used.format.rowHeight=66;used.format.wrapText=true;used.format.font={name:'Aptos',size:11,color:'#24383D'};
  for(let i=0;i<columns.length;i++)sh.getRangeByIndexes(0,i,rows.length+5,1).format.columnWidthPx=widths[i]??250;
  sh.getRange('A1:F1').merge();sh.getRange('A1').values=[[`ReRouteHer | MASCO 2020 — ${name}`]];
  sh.getRange('A1:F1').format.fill='#164B55';sh.getRange('A1').format.font={size:19,bold:true,color:'#FFFFFF'};
  sh.getRange('A2:F2').merge();
  sh.getRange('A2').values=[[name==='Excluded'?'Excluded conservatively: no verified equivalent, non-unique aggregate, or unavailable 2020 grade. Not proof that these professions did not exist.':'Six-digit MASCO 2020 identities; current STEM membership and D11 profiles inherited. Test use only; ESCO mappings are project proxies.']];
  sh.getRange('A2:F2').format.fill='#E9F2F1';
  sh.getRange(`A1:${letter(columns.length-1)}1`).format.rowHeightPx=52;
  sh.getRange(`A2:${letter(columns.length-1)}2`).format.rowHeightPx=54;
  sh.getRange(`A3:${letter(columns.length-1)}4`).format.rowHeightPx=14;
  sh.getRangeByIndexes(4,0,1,columns.length).format.fill='#164B55';
  sh.getRangeByIndexes(4,0,1,columns.length).format.font={bold:true,color:'#FFFFFF'};
  sh.tables.add(`A5:${letter(columns.length-1)}${rows.length+5}`,true,name.replaceAll(' ','')+'Data');
  for(let i=0;i<rows.length;i++)if(i%2===1)sh.getRangeByIndexes(i+5,0,1,columns.length).format.fill='#F1F6F5';
  if(['Excluded','Crosswalk'].includes(name))sh.getRangeByIndexes(5,9,rows.length,1).format.rowHeight=96;
}
overview.showGridLines=false;
overview.getRange('A1:E24').format.font={name:'Aptos',size:12,color:'#24383D'};
overview.getRange('A1:E24').format.rowHeight=38;overview.getRange('A1:E24').format.wrapText=true;
for(const [col,width] of [['A',320],['B',110],['C',170],['D',170],['E',170]])overview.getRange(`${col}1:${col}24`).format.columnWidthPx=width;
overview.getRange('A1:E1').merge();overview.getRange('A1').values=[['ReRouteHer | MASCO 2020 STEM release']];
overview.getRange('A1:E1').format.fill='#164B55';overview.getRange('A1').format.font={size:21,bold:true,color:'#FFFFFF'};
overview.getRange('A1:E1').format.rowHeight=55;
overview.getRange('A2:E2').merge();overview.getRange('A2').values=[['30 August 2026 • Six-digit roles • D11 structure retained • ESCO comparison preserved']];
overview.getRange('A4:B4').values=[['Scope reconciliation','Count']];overview.getRange('C4:E4').merge();overview.getRange('C4').values=[['Meaning']];
overview.getRange('A4:E4').format.fill='#164B55';overview.getRange('A4:E4').format.font={bold:true,color:'#FFFFFF'};
const metrics=[
 ['Original current STEM roles',"=COUNTA('ESCO comparison'!A6:A662)",'All current source records preserved in the comparison audit.'],
 ['Retained source roles',"=COUNTIF('ESCO comparison'!D6:D662,\"retained\")",'Original occupations with a reviewed 2020 counterpart.'],
 ['Excluded source roles',"=COUNTA('Excluded'!A6:A24)",'14 unverified equivalents, 4 broad aggregates, 1 grade gap.'],
 ['Extra rows from combined titles',"=COUNTA('Crosswalk'!A6:A680)-B5",'15 combined source roles expand into separate 2020 entries.'],
 ['Duplicate target rows merged',"=COUNTIF('Crosswalk'!G6:G680,\"retained\")-B10",'One shared target keeps the exact-title source as its main profile.'],
 ['Final unique MASCO 2020 roles',"=COUNTA('Retained'!A6:A660)",'638 retained + 18 split additions − 1 duplicate = 655.'],
 ['Final roles with ESCO codes',"=COUNTA('Retained'!J6:J660)",'All retained roles keep an inherited ESCO assignment.'],
];
for(let i=0;i<metrics.length;i++){const n=i+5,[label,formula,note]=metrics[i];overview.getRange(`A${n}`).values=[[label]];overview.getRange(`B${n}`).formulas=[[formula]];overview.getRange(`C${n}:E${n}`).merge();overview.getRange(`C${n}`).values=[[note]];}
overview.getRange('B5:B11').setNumberFormat('#,##0');overview.getRange('B5:B11').format.font={size:17,bold:true,color:'#164B55'};
overview.getRange('A10:E10').format.fill='#DCEDEA';
const notes=[
 [13,'Important limitations'],
 [14,'MASCO 2020 code/title identities are verified against the official index. STEM membership comes from the current official portal category, not a historical 2020 STEM tag.'],
 [16,'Task statements, remote-work and AI pre-ratings are inherited current D11 test profiles. Splits and functional matches require review before production use.'],
 [18,'No live database changes or model retraining/deployment. Existing numeric role IDs can refer to different occupations across versions; do not blindly append this release.'],
 [20,'Official reference: https://www.dosm.gov.my/uploads/content-downloads/file_20220920110308.pdf'],
 [22,'Grade-family reference: https://docs.jpa.gov.my/docs/sspa/SSPA_LAMPIRAN_B.pdf'],
 [24,'Full CSV package includes 6,051 skills, 37,521 aliases, 41,286 role-skill links, 5,512 inherited tasks, embeddings, exclusions and reproducibility files.'],
];
for(const [n,note] of notes){overview.getRange(`A${n}:E${n}`).merge();overview.getRange(`A${n}`).values=[[note]];overview.getRange(`A${n}:E${n}`).format.rowHeight=n===13?32:55;}
overview.getRange('A13:E13').format.fill='#164B55';overview.getRange('A13').format.font={bold:true,color:'#FFFFFF'};
const counts=overview.getRange('B5:B11').values.flat();
if(JSON.stringify(counts)!==JSON.stringify([657,638,19,18,1,655,655]))throw new Error('Summary formula mismatch '+JSON.stringify(counts));
const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A',options:{useRegex:true,maxResults:20},maxChars:1500});
await fs.writeFile(path.join(root,'02_QA/workbook_formula_check.json'),JSON.stringify({counts,scan:errors.ndjson},null,2)+'\n');
for(const [name,range] of [['Summary','A1:E24'],['Retained','A1:F9'],['Excluded','A1:J9'],['Crosswalk','A1:J9'],['ESCO comparison','A1:G9']]){
  const blob=await wb.render({sheetName:name,range,scale:1.3,format:'png'});
  await fs.writeFile(path.join(previews,name.replaceAll(' ','_')+'.png'),new Uint8Array(await blob.arrayBuffer()));
}
const outputDir=path.join(path.dirname(root),'outputs/01a047e7-ceba-7df3-8d1a-ba8071e66430');await fs.mkdir(outputDir,{recursive:true});
const output=await SpreadsheetFile.exportXlsx(wb);await output.save(path.join(outputDir,'MASCO2020_STEM_Review.xlsx'));
console.log(JSON.stringify({workbook:path.join(outputDir,'MASCO2020_STEM_Review.xlsx'),counts}));
