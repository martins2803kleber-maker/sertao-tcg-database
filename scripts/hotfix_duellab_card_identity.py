from pathlib import Path

p = Path('duellab/web/app.js')
s = p.read_text(encoding='utf-8')
marker = '/* HOTFIX OCGCORE CARD IDENTITY */'
if marker in s:
    raise SystemExit(0)

needle = "    const style=document.createElement('style');"
if needle not in s:
    raise SystemExit('app.js insertion point not found')

patch = r'''    /* HOTFIX OCGCORE CARD IDENTITY */
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

'''

s = s.replace(needle, patch + needle, 1)
p.write_text(s, encoding='utf-8')
