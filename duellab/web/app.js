(async function(){
  const status=document.querySelector('#engineStatus');
  const files=['01.txt','02.txt','03.txt','04.txt','05.txt','06.txt'];
  try{
    let source='';
    for(let i=0;i<files.length;i++){
      if(status)status.textContent='Carregando Duel Lab '+(i+1)+'/'+files.length+'...';
      const r=await fetch('./chunks/'+files[i],{cache:'no-cache'});
      if(!r.ok)throw new Error(files[i]+' HTTP '+r.status);
      source+=await r.text();
    }

    source=source.replace("var REAL_BASE='../../assets/duellab/';","var REAL_BASE='https://cdn.jsdelivr.net/gh/martins2803kleber-maker/sertao-tcg-database@6d321c117c77f000a78274fb8c72c1a727f9533c/assets/duellab/';");

    /* IDs exatos sempre vencem alias/baseId. */
    source=source.replace(`      state.byId=new Map();\n      data.forEach(function(c){\n        [c.id,c.baseId,c.originalId].filter(Boolean).forEach(function(id){state.byId.set(String(id),c)});\n      });`,`      state.byId=new Map();\n      data.forEach(function(c){if(c&&c.id!=null)state.byId.set(String(c.id),c)});\n      data.forEach(function(c){[c.baseId,c.originalId].filter(Boolean).forEach(function(id){var k=String(id);if(!state.byId.has(k))state.byId.set(k,c)})});`);

    /* MSG_DRAW moderno: code(u32)+position(u32). */
    source=source.replace("for(var d=0;d<n&&o2+4<=pkt.length;d++){codes.push(u32(dv,o2));o2+=4}","for(var d=0;d<n&&o2+8<=pkt.length;d++){codes.push(u32(dv,o2));o2+=8}");

    /* Nunca deixa uma leitura errada de MSG_DRAW puxar uma carta do Extra para a mão. */
    source=source.replace(/function mirrorDraw\(side,codes\)\{[\s\S]*?\n\}\n\nfunction locPool/,`function mirrorDraw(side,codes){
  var hand=side===0?state.playerHand:state.botHand;
  var deck=side===0?state.playerDeck:state.botDeck;
  var extra=side===0?state.playerExtra:state.botExtra;
  codes.forEach(function(code){
    var ix=deck.findIndex(function(c){return Number(c&&c.id)===Number(code)});
    var inExtra=(extra||[]).some(function(c){return Number(c&&c.id)===Number(code)});
    var card=null;
    if(ix>=0)card=deck.splice(ix,1)[0];
    else if(inExtra){
      console.warn('Duel Lab bloqueou compra inválida do Extra Deck:',code);
      if(deck.length)card=deck.shift();
    }else card=cardByCode(code);
    if(card)hand.push(card);
  });
  render();
}

function locPool`);

    /* Estado interno completo: 5 MMZ + 2 EMZ e S/T 0..7. O renderer mostra só
       as cinco zonas normais e desenha EMZ/Field separadamente. */
    source=source.replace("var slot=(seq!=null&&seq>=0&&seq<5)?seq:pool.findIndex(function(x){return !x});","var slot=(seq!=null&&seq>=0&&seq<pool.length)?seq:pool.findIndex(function(x){return !x});");

    source=source.replace("'proc_workaround.lua'\n];","'proc_workaround.lua','proc_persistent.lua','proc_rush.lua','proc_skill.lua'\n];");

    /* CardScripts ficam locais no próprio Duel Lab. O workflow gera core.json
       e 256 shards. Se o bundle ainda não estiver publicado, usa Project Ignis
       remoto como fallback, sem quebrar o duelo. */
    source=source.replace(/async function fetchLuaExact\(path\)\{[\s\S]*?\n\}/,`var localCoreScripts=null,localScriptShards=new Map();
async function localScriptBundle(path){
  var leaf=String(path||'').split('/').pop(),m=/^c(\\d+)\\.lua$/i.exec(leaf),url;
  if(m){
    var shard=Number(m[1]).toString(16).padStart(8,'0').slice(0,2);
    if(localScriptShards.has(shard))return localScriptShards.get(shard);
    url='./cardscripts/shards/'+shard+'.json';
    try{var r=await fetch(url,{cache:'force-cache'});if(!r.ok)return null;var j=await r.json();localScriptShards.set(shard,j);return j}catch(e){return null}
  }
  if(localCoreScripts)return localCoreScripts;
  try{var r2=await fetch('./cardscripts/core.json',{cache:'force-cache'});if(!r2.ok)return null;localCoreScripts=await r2.json();return localCoreScripts}catch(e){return null}
}
async function fetchLuaExact(path){
  var local=await localScriptBundle(path);
  if(local&&local.files&&Object.prototype.hasOwnProperty.call(local.files,path))return local.files[path];
  var r=await fetch(CARD_SCRIPT_BASE+path,{cache:'force-cache'});
  if(!r.ok)throw Error(path+' '+r.status);
  return r.text();
}`);

    /* Remove zonas duplicadas herdadas do protótipo antigo. */
    source=source.replace("  h+='<div class=\"stdl-zone\">EMZ</div><div class=\"stdl-zone\">EMZ</div>';\n  el.innerHTML=h;","  el.innerHTML=h;");
    source=source.replace("  h+='<div class=\"stdl-zone\">FIELD</div><div class=\"stdl-zone\">P</div>';\n  $(id).innerHTML=h;","  $(id).innerHTML=h;");

    source=source.replace(`function setupMirrorFromDecks(player,bot){\n  state.playerLP=8000;state.botLP=8000;state.playerField=Array(5).fill(null);state.botField=Array(5).fill(null);\n  state.playerHand=[];state.botHand=[];state.playerDeck=player.main.map(cardByCode);state.botDeck=(bot.main||[]).map(cardByCode);state.playerSpellField=Array(5).fill(null);state.botSpellField=Array(5).fill(null);`,`function cloneCardByCode(id){return Object.assign({},cardByCode(id))}
function shuffleMirrorArray(a){
  if(!a||a.length<2)return a;
  var rnd=new Uint32Array(a.length);try{crypto.getRandomValues(rnd)}catch(e){for(var q=0;q<rnd.length;q++)rnd[q]=(Math.random()*0xffffffff)>>>0}
  for(var i=a.length-1;i>0;i--){var j=rnd[i]%(i+1),t=a[i];a[i]=a[j];a[j]=t}
  return a;
}
function setupMirrorFromDecks(player,bot){
  state.playerLP=8000;state.botLP=8000;state.playerField=Array(7).fill(null);state.botField=Array(7).fill(null);
  state.playerHand=[];state.botHand=[];state.playerDeck=shuffleMirrorArray(player.main.map(cloneCardByCode));state.botDeck=shuffleMirrorArray((bot.main||[]).map(cloneCardByCode));state.playerSpellField=Array(8).fill(null);state.botSpellField=Array(8).fill(null);`);
    source=source.replace("state.playerExtra=(player.extra||[]).map(cardByCode);state.botExtra=(bot.extra||[]).map(cardByCode);","state.playerExtra=(player.extra||[]).map(cloneCardByCode);state.botExtra=(bot.extra||[]).map(cloneCardByCode);");

    /* Corrige sequence da mão para cópias repetidas da mesma carta. */
    source=source.replace("state.playerHand.forEach(function(c){","state.playerHand.forEach(function(c,handIndex){");
    source=source.replace("b.setAttribute('data-sequence',String(state.playerHand.indexOf(c)));","b.setAttribute('data-sequence',String(handIndex));");

    /* OCGCore moderno, conforme parser non-compat do EDOPro. */
    source=source.replace(/function parseIdle\(pkt\)\{[\s\S]*?\n\}\nfunction parseBattle\(pkt\)\{/,`function parseIdle(pkt){
  var dv=new DataView(pkt.buffer,pkt.byteOffset,pkt.byteLength),o=1;
  var player=dv.getUint8(o++);
  function count32(){var n=u32(dv,o);o+=4;return n}
  function refs(seq32,activate){
    var n=count32(),a=[];
    for(var i=0;i<n;i++){
      var c=readCardRef(dv,o,seq32);o=c.next;
      if(activate){c.description=u64num(dv,o);o+=8;c.clientMode=dv.getUint8(o++)}
      a.push(c);
    }
    return a;
  }
  var summon=refs(true,false),special=refs(true,false),reposition=refs(false,false),mset=refs(true,false),sset=refs(true,false),activate=refs(true,true);
  return {msg:11,player:player,summon:summon,special:special,reposition:reposition,mset:mset,sset:sset,activate:activate,toBP:!!dv.getUint8(o++),toEP:!!dv.getUint8(o++),shuffle:!!dv.getUint8(o++)};
}
function parseBattle(pkt){`);

    source=source.replace(/function parseBattle\(pkt\)\{[\s\S]*?\n\}\n\nfunction parseChain\(pkt\)\{/,`function parseBattle(pkt){
  var dv=new DataView(pkt.buffer,pkt.byteOffset,pkt.byteLength),o=1,player=dv.getUint8(o++);
  var na=u32(dv,o);o+=4,battleAct=[];
  for(var i=0;i<na;i++){var c=readCardRef(dv,o,true);o=c.next;c.description=u64num(dv,o);o+=8;c.clientMode=dv.getUint8(o++);battleAct.push(c)}
  var nb=u32(dv,o);o+=4,attackers=[];
  for(var j=0;j<nb;j++){var c2=readCardRef(dv,o,false);o=c2.next;c2.direct=!!dv.getUint8(o++);attackers.push(c2)}
  return {msg:10,player:player,activate:battleAct,attack:attackers,toM2:!!dv.getUint8(o++),toEP:!!dv.getUint8(o++)};
}

function parseChain(pkt){`);

    source=source.replace(/function parseChain\(pkt\)\{[\s\S]*?\n\}\nfunction parseSelectCards/,`function parseChain(pkt){
  var dv=new DataView(pkt.buffer,pkt.byteOffset,pkt.byteLength),o=1;
  var player=dv.getUint8(o++),spe=dv.getUint8(o++),forced=!!dv.getUint8(o++);
  var hintSelf=u32(dv,o);o+=4,hintOpp=u32(dv,o);o+=4,n=u32(dv,o);o+=4,chains=[];
  for(var i=0;i<n;i++){
    var code=u32(dv,o);o+=4,controller=dv.getUint8(o++),location=dv.getUint8(o++),sequence=u32(dv,o);o+=4,position=u32(dv,o);o+=4;
    var description=u64num(dv,o);o+=8,clientMode=dv.getUint8(o++);
    chains.push({code:code,controller:controller,location:location,sequence:sequence,position:position,description:description,clientMode:clientMode});
  }
  return {msg:16,player:player,speCount:spe,forced:forced,hintSelf:hintSelf,hintOpp:hintOpp,chains:chains,cancelable:!forced};
}
function parseSelectCards`);

    /* SORT_CARD/SORT_CHAIN também usam location=u8 no loc-info moderno. */
    source=source.replace(/function parseSort\(pkt,msg\)\{[\s\S]*?\n\}/,`function parseSort(pkt,msg){
  var dv=new DataView(pkt.buffer,pkt.byteOffset,pkt.byteLength),o=1,player=dv.getUint8(o++),n=u32(dv,o);o+=4,cards=[];
  for(var i=0;i<n;i++){var code=u32(dv,o);o+=4,controller=dv.getUint8(o++),location=dv.getUint8(o++),sequence=u32(dv,o);o+=4;cards.push({code:code,controller:controller,location:location,sequence:sequence})}
  return {msg:msg,player:player,cards:cards};
}`);

    /* Render dedicado das EMZ e Field Zone; o grid principal continua com 5+5. */
    source=source.replace("function render(){",`function renderAuxZone(id,c,label,side,location,sequence,extraClass){
  var el=$(id);if(!el)return;
  el.className='stdl-zone '+(extraClass||'');
  ['previewKey','cardCode','side','location','sequence'].forEach(function(k){delete el.dataset[k]});
  if(!c){el.textContent=label;return}
  var key=previewKey(c),u=img(c);state.previewMap.set(key,c);
  el.classList.add('occupied');el.dataset.previewKey=key;el.dataset.cardCode=String(c.id||c.originalId||c.baseId||'');el.dataset.side=String(side);el.dataset.location=String(location);el.dataset.sequence=String(sequence);
  el.innerHTML=(u?'<div class="stdl-card-fit"><img alt="" src="'+u+'"></div>':'<div class="stdl-card-fit-fallback">'+escapeHtml(cardName(c))+'</div>')+'<span class="stdl-atk">'+atk(c)+'</span>';
}
function renderAuxZones(){
  var lc=state.playerField[5]||state.botField[6],ls=state.playerField[5]?0:1,lseq=state.playerField[5]?5:6;
  var rc=state.playerField[6]||state.botField[5],rs=state.playerField[6]?0:1,rseq=state.playerField[6]?6:5;
  renderAuxZone('#extraMonsterZoneLeft',lc,'EMZ',ls,4,lseq,'stdl-emz-zone');
  renderAuxZone('#extraMonsterZoneRight',rc,'EMZ',rs,4,rseq,'stdl-emz-zone');
  renderAuxZone('#playerFieldZone',state.playerSpellField[5],'FIELD',0,8,5,'stdl-static-zone stdl-field-zone player-static');
  renderAuxZone('#botFieldZone',state.botSpellField[5],'FIELD',1,8,5,'stdl-static-zone stdl-field-zone bot-static');
}
function render(){`);
    source=source.replace("renderField('#playerMonsters',state.playerField,'MONSTER','0');renderSpell('#playerSpell',state.playerSpellField,'0');","renderField('#playerMonsters',state.playerField,'MONSTER','0');renderSpell('#playerSpell',state.playerSpellField,'0');renderAuxZones();");

    source=source.replace("if(msg===50){mirrorMovePacket(pkt)}",`if(msg===32){var pl=dv.getUint8(1),deck=pl===0?state.playerDeck:state.botDeck;shuffleMirrorArray(deck);render()}else if(msg===33){var hp=dv.getUint8(1),hand=hp===0?state.playerHand:state.botHand;shuffleMirrorArray(hand);render()}else if(msg===50){mirrorMovePacket(pkt)}`);

    source=source.replace(`passChainBtn.onclick=function(){\n  if(real.pending&&real.pending.msg===16&&!real.pending.forced){respondInt(-1);real.pending=null;updatePromptUI();pumpReal()}\n};`,`var shuffleDeckBtn=document.createElement('button');shuffleDeckBtn.type='button';shuffleDeckBtn.textContent='SHUFFLE DECK';shuffleDeckBtn.hidden=true;shuffleDeckBtn.className='secondary';if(passChainBtn&&passChainBtn.parentNode)passChainBtn.parentNode.insertBefore(shuffleDeckBtn,passChainBtn.nextSibling);shuffleDeckBtn.onclick=function(){if(real.pending&&real.pending.msg===11&&real.pending.player===0&&real.pending.shuffle){respondInt(8);real.pending=null;updatePromptUI();pumpReal()}};passChainBtn.onclick=function(){if(real.pending&&real.pending.msg===16&&!real.pending.forced){respondInt(-1);real.pending=null;updatePromptUI();pumpReal()}};`);

    source=source.replace("passChainBtn.hidden=true;",`passChainBtn.hidden=true;if(typeof shuffleDeckBtn!=='undefined')shuffleDeckBtn.hidden=!(p&&p.msg===11&&p.player===0&&p.shuffle);var ep=$('#playerExtraPile');if(ep){var extraLegal=!!(p&&p.player===0&&p.msg===11&&(p.special||[]).some(function(x){return Number(x.location)===64}));ep.classList.toggle('legal-active',extraLegal);}`);

    source=source.replace("var startRealBtn=$('#startRealBtn');if(startRealBtn)startRealBtn.onclick=startRealDuel;",`document.querySelectorAll('#phaseBar button').forEach(function(btn){btn.onclick=function(){if(!real.active||!real.pending||real.pending.player!==0)return;var ph=btn.dataset.phase,p=real.pending;if(p.msg===11){if(ph==='BP'&&p.toBP){respondInt(6);real.pending=null;updatePromptUI();pumpReal()}else if(ph==='EP'&&p.toEP){respondInt(7);real.pending=null;updatePromptUI();pumpReal()}}else if(p.msg===10){if(ph==='M2'&&p.toM2){respondInt(2);real.pending=null;updatePromptUI();pumpReal()}else if(ph==='EP'&&p.toEP){respondInt(3);real.pending=null;updatePromptUI();pumpReal()}}}});var startRealBtn=$('#startRealBtn');if(startRealBtn)startRealBtn.onclick=startRealDuel;`);

    source=source.replace("while(real.active&&safety++<240)","while(real.active&&safety++<800)");
    source=source.replace("if(safety>=240)throw Error('Safety stop: core avançou demais sem solicitar decisão.');","if(safety>=800)throw Error('Safety stop: core avançou demais sem solicitar decisão.');");

    /* HOTFIX OCGCORE CARD IDENTITY */
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

    const style=document.createElement('style');
    style.textContent='#playerExtraPile.legal-active{outline:2px solid #4fd8ff;box-shadow:0 0 18px rgba(79,216,255,.55)}';
    document.head.appendChild(style);

    new Function(source+'\n//# sourceURL=duellab-runtime.js')();
  }catch(error){
    console.error(error);
    if(status)status.textContent='Erro ao carregar Duel Lab: '+(error.message||error);
  }
})();