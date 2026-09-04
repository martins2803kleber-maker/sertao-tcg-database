from pathlib import Path

p = Path('duellab/web/app.js')
s = p.read_text(encoding='utf-8')
needle = "    const style=document.createElement('style');"
if needle not in s:
    raise SystemExit('app.js insertion point not found')

patches = []

if '/* HOTFIX OCGCORE CARD IDENTITY */' not in s:
    patches.append(r'''    /* HOTFIX OCGCORE CARD IDENTITY */
    source=source.replace(/function sameRef\(a,b\)\{[\s\S]*?\n\}/,`function sameRef(a,b){
  if(!a||!b)return false;
  var al=a.location!=null?Number(a.location):null,bl=b.location!=null?Number(b.location):null;
  var ac=a.controller!=null?Number(a.controller):null,bc=b.controller!=null?Number(b.controller):null;
  var as=a.sequence!=null?Number(a.sequence):null,bs=b.sequence!=null?Number(b.sequence):null;
  if(ac!=null&&bc!=null&&ac!==bc)return false;
  if(al!=null&&bl!=null&&al!==bl)return false;
  if(al!=null&&bl!=null&&as!=null&&bs!=null)return as===bs;
  var ca=Number(a.code||0),cb=Number(b.code||0);
  return !!ca&&!!cb&&ca===cb;
}`);
    source=source.replace("if(p.msg===11)duelHint.textContent='MAIN PHASE - right-click a card to Summon, Set or Activate.';",`if(p.msg===11){duelHint.textContent='MAIN PHASE - right-click a card to Summon, Set or Activate.';console.debug('Duel Lab legal idle',p)}`);

''')

if '/* LOCAL PROJECT IGNIS CORE DB V2 */' not in s:
    patches.append(r'''    /* LOCAL PROJECT IGNIS CORE DB V2 */
    source=source.replace("fetch(REAL_BASE+'core/cards_core.json'+bust,{cache:'force-cache'})", "fetch('./core/cards_core.json',{cache:'no-cache'}).then(function(localResponse){if(localResponse.ok)return localResponse;return fetch(REAL_BASE+'core/cards_core.json'+bust,{cache:'force-cache'})})");
    source=source.replace("if(rec.length<Math.min(20,new Set(ids).size))throw Error('Dados do core incompletos para este deck.');", `var uniqueCoreIds=Array.from(new Set(ids.map(Number))).filter(Boolean);\n    var coreHave=new Set(rec.map(function(c){return Number(c.id)}));\n    var missingCoreIds=uniqueCoreIds.filter(function(id){return !coreHave.has(id)});\n    if(missingCoreIds.length)throw Error('Banco OCGCore sem dados para '+missingCoreIds.length+' carta(s): '+missingCoreIds.slice(0,20).join(', '));\n    log('<b>Core DB:</b> '+rec.length+' cartas do duelo validadas.');`);
    source=source.replace("real.ready=true;", "real.ready=true;console.info('Duel Lab Core DB carregado:',real.coreCards.length,'cartas');");

''')

if patches:
    s = s.replace(needle, ''.join(patches) + needle, 1)
    p.write_text(s, encoding='utf-8')
else:
    print('hotfixes already installed')
