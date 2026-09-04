import fs from 'node:fs';
import path from 'node:path';
import {execFileSync} from 'node:child_process';

const input=process.argv[2]||'/tmp/cardscripts';
const output=process.argv[3]||'duellab/web/cardscripts';
const roots=['','official','pre-errata','goat','unofficial'];
const rootRank=new Map(roots.map((r,i)=>[r,i]));

function walk(dir){
  const out=[];
  for(const ent of fs.readdirSync(dir,{withFileTypes:true})){
    const p=path.join(dir,ent.name);
    if(ent.isDirectory())out.push(...walk(p));
    else if(ent.isFile()&&ent.name.endsWith('.lua'))out.push(p);
  }
  return out;
}
function rel(p){return path.relative(input,p).split(path.sep).join('/');}
function rank(p){
  const first=p.includes('/')?p.slice(0,p.indexOf('/')):'';
  return rootRank.has(first)?rootRank.get(first):99;
}
function shardFor(name){
  const m=/^c(\d+)\.lua$/i.exec(name);
  if(!m)return null;
  return Number(m[1]).toString(16).padStart(8,'0').slice(0,2);
}
function addIndex(index,name,p){
  if(!index[name])index[name]=[];
  index[name].push(p);
}

fs.rmSync(output,{recursive:true,force:true});
fs.mkdirSync(path.join(output,'shards'),{recursive:true});

const core={files:{},byName:{}};
const shards=new Map();
let cardCount=0,coreCount=0;

for(const abs of walk(input)){
  const rp=rel(abs),name=path.posix.basename(rp),src=fs.readFileSync(abs,'utf8');
  const shard=shardFor(name);
  if(shard){
    if(!shards.has(shard))shards.set(shard,{files:{},byName:{}});
    const obj=shards.get(shard);
    obj.files[rp]=src;addIndex(obj.byName,name,rp);cardCount++;
  }else{
    core.files[rp]=src;addIndex(core.byName,name,rp);coreCount++;
  }
}

for(const obj of [core,...shards.values()]){
  for(const arr of Object.values(obj.byName))arr.sort((a,b)=>rank(a)-rank(b)||a.localeCompare(b));
}

fs.writeFileSync(path.join(output,'core.json'),JSON.stringify(core));
for(const [id,obj] of [...shards.entries()].sort(([a],[b])=>a.localeCompare(b))){
  fs.writeFileSync(path.join(output,'shards',id+'.json'),JSON.stringify(obj));
}

let upstream='unknown';
try{upstream=execFileSync('git',['-C',input,'rev-parse','HEAD'],{encoding:'utf8'}).trim();}catch{}
fs.writeFileSync(path.join(output,'manifest.json'),JSON.stringify({
  source:'ProjectIgnis/CardScripts',upstream,generatedAt:new Date().toISOString(),
  coreFiles:coreCount,cardFiles:cardCount,shards:shards.size
}));
console.log(`Generated ${coreCount} core scripts + ${cardCount} card scripts in ${shards.size} shards`);
