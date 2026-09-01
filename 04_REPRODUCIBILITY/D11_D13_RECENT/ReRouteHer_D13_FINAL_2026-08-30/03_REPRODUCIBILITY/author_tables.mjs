// Author machine-readable CSV matrices with the supported artifact workbook API.
// CSV has no display formatting. Previews are QA samples, not alternate datasets.
import fs from 'node:fs/promises';
import path from 'node:path';
import {Workbook} from '@oai/artifact-tool';

const root=process.argv[2];
if(!root) throw new Error('Pass the absolute release directory');
const payload=JSON.parse(await fs.readFile(path.join(root,'02_QA/table_payloads.json'),'utf8'));
const qa=[];
const quote=v=>'"'+String(v??'').replaceAll('"','""')+'"';
const csvLine=row=>row.map(quote).join(',')+'\r\n';
const escapeText=v=>typeof v==='string' && /^\d{4}-\d\d-\d\dT/.test(v);
await fs.mkdir(path.join(root,'02_QA/previews'),{recursive:true});
for(const [rel,{columns,rows}] of Object.entries(payload)){
  const wb=Workbook.create(); const sh=wb.worksheets.add('Data');
  sh.getRangeByIndexes(0,0,1,columns.length).values=[columns];
  for(let k=0;k<columns.length;k++)if(typeof rows[0][k]==='string')
    sh.getRangeByIndexes(1,k,rows.length,1).setNumberFormat('@');
  // Bounded block writes and round-trip checks keep every identifier as text.
  for(let i=0;i<rows.length;i+=2000){
    const block=rows.slice(i,i+2000);
    // Preserve the exact source timestamp spelling instead of ISO date coercion.
    sh.getRangeByIndexes(i+1,0,block.length,columns.length).values=block.map(row=>row.map(v=>escapeText(v)?"'"+v:v));
  }
  const chunks=[csvLine(columns)];
  for(let i=0;i<rows.length;i+=2000){
    const original=rows.slice(i,i+2000);
    const actual=sh.getRangeByIndexes(i+1,0,original.length,columns.length).values;
    for(let j=0;j<original.length;j++)for(let k=0;k<columns.length;k++){
      if(escapeText(original[j][k]) && actual[j][k]==="'"+original[j][k])actual[j][k]=actual[j][k].slice(1);
      if(String(actual[j][k]??'')!==String(original[j][k]??''))throw new Error(`Round-trip mismatch ${rel}:${i+j}:${columns[k]}`);
    }
    chunks.push(...actual.map(csvLine));
  }
  const target=path.join(root,rel);await fs.mkdir(path.dirname(target),{recursive:true});
  await fs.writeFile(target,chunks.join(''),'utf8');
  // Compact overview of representative fields, never a clipped embedding string.
  const pv=Workbook.create(); const ps=pv.worksheets.add('Preview');
  const selected=columns.map((c,i)=>({c,i})).filter(x=>!['embedding','masco_tasks','masco_description','esco_description','esco_alternate_labels'].includes(x.c)).slice(0,6);
  const sample=[selected.map(x=>x.c),...rows.slice(0,4).map(row=>selected.map(x=>row[x.i]))];
  const range=ps.getRangeByIndexes(0,0,sample.length,selected.length);range.values=sample;
  range.format.columnWidth=190;range.format.rowHeight=72;range.format.wrapText=true;
  ps.getRangeByIndexes(0,0,1,selected.length).format.fill='#164B55';
  ps.getRangeByIndexes(0,0,1,selected.length).format.font={bold:true,color:'#FFFFFF'};
  // Wider title/text fields in QA previews; identifiers remain visible in full.
  for(let i=0;i<selected.length;i++)if(/title|name|uri|rationale|issue/.test(selected[i].c))ps.getRangeByIndexes(0,i,sample.length,1).format.columnWidth=310;
  const image=await pv.render({sheetName:'Preview',range:`A1:${String.fromCharCode(64+selected.length)}${sample.length}`,scale:1.3,format:'png'});
  await fs.writeFile(path.join(root,'02_QA/previews',path.basename(rel,'.csv')+'.png'),new Uint8Array(await image.arrayBuffer()));
  const errors=await pv.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A',options:{useRegex:true,maxResults:5},maxChars:500});
  qa.push({file:rel,rows:rows.length,columns:columns.length,round_trip:'PASS',preview_scan:errors.ndjson});
  console.log(JSON.stringify({file:rel,rows:rows.length,round_trip:'PASS'}));
}
await fs.writeFile(path.join(root,'02_QA/artifact_authoring_checks.json'),JSON.stringify(qa,null,2)+'\n');
