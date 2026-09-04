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

    source=source.replace(`      state.byId=new Map();\n      data.forEach(function(c){\n        [c.id,c.baseId,c.originalId].filter(Boolean).forEach(function(id){state.byId.set(String(id),c)});\n      });`,`      state.byId=new Map();\n      data.forEach(function(c){if(c&&c.id!=null)state.byId.set(String(c.id),c)});\n      data.forEach(function(c){[c.baseId,c.originalId].filter(Boolean).forEach(function(id){var k=String(id);if(!state.byId.has(k))state.byId.set(k,c)})});`);

    source=source.replace("for(var d=0;d<n&&o2+4<=pkt.length;d++){codes.push(u32(dv,o2));o2+=4}","for(var d=0;d<n&&o2+8<=pkt.length;d++){codes.push(u32(dv,o2));o2+=8}");

    /* Keep the visual field arrays at the original five zones. Extra Monster
       Zones and Field/Pendulum zones are rendered by their own DOM elements;
       expanding these arrays changes the CSS grid and duplicates zones. */
    source=source.replace("'proc_workaround.lua'\n];","'proc_workaround.lua','proc_persistent.lua','proc_rush.lua','proc_skill.lua'\n];");

    source=source.replace(`function setupMirrorFromDecks(player,bot){\n  state.playerLP=8000;state.botLP=8000;state.playerField=Array(5).fill(null);state.botField=Array(5).fill(null);\n  state.playerHand=[];state.botHand=[];state.playerDeck=player.main.map(cardByCode);state.botDeck=(bot.main||[]).map(cardByCode);state.playerSpellField=Array(5).fill(null);state.botSpellField=Array(5).fill(null);`,`function shuffleMirrorArray(a){\n  if(!a||a.length<2)return a;\n  var rnd=new Uint32Array(a.length);try{crypto.getRandomValues(rnd)}catch(e){for(var q=0;q<rnd.length;q++)rnd[q]=(Math.random()*0xffffffff)>>>0}\n  for(var i=a.length-1;i>0;i--){var j=rnd[i]%(i+1),t=a[i];a[i]=a[j];a[j]=t}\n  return a;\n}\nfunction setupMirrorFromDecks(player,bot){\n  state.playerLP=8000;state.botLP=8000;state.playerField=Array(5).fill(null);state.botField=Array(5).fill(null);\n  state.playerHand=[];state.botHand=[];state.playerDeck=shuffleMirrorArray(player.main.map(cardByCode));state.botDeck=shuffleMirrorArray((bot.main||[]).map(cardByCode));state.playerSpellField=Array(5).fill(null);state.botSpellField=Array(5).fill(null);`);

    /* OCGCore moderno conforme o parser non-compat do EDOPro. */
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
  var summon=refs(true,false);
  var special=refs(true,false);
  var reposition=refs(false,false);
  var mset=refs(true,false);
  var sset=refs(true,false);
  var activate=refs(true,true);
  var out={msg:11,player:player,summon:summon,special:special,reposition:reposition,mset:mset,sset:sset,activate:activate,toBP:!!dv.getUint8(o++),toEP:!!dv.getUint8(o++),shuffle:!!dv.getUint8(o++)};
  console.debug('Duel Lab SELECT_IDLECMD',out);
  return out;
}
function parseBattle(pkt){`);

    source=source.replace(/function parseBattle\(pkt\)\{[\s\S]*?\n\}\n\nfunction parseChain\(pkt\)\{/,`function parseBattle(pkt){
  var dv=new DataView(pkt.buffer,pkt.byteOffset,pkt.byteLength),o=1,player=dv.getUint8(o++);
  var na=u32(dv,o);o+=4,act=[];
  for(var i=0;i<na;i++){var c=readCardRef(dv,o,true);o=c.next;c.description=u64num(dv,o);o+=8;c.clientMode=dv.getUint8(o++);act.push(c)}
  var nb=u32(dv,o);o+=4,atk=[];
  for(var j=0;j<nb;j++){var c2=readCardRef(dv,o,false);o=c2.next;c2.direct=!!dv.getUint8(o++);atk.push(c2)}
  return {msg:10,player:player,activate:act,attack:atk,toM2:!!dv.getUint8(o++),toEP:!!dv.getUint8(o++)};
}

function parseChain(pkt){`);

    source=source.replace("if(msg===50){mirrorMovePacket(pkt)}",`if(msg===32){var pl=dv.getUint8(1),deck=pl===0?state.playerDeck:state.botDeck;shuffleMirrorArray(deck);render();log((pl===0?'Seu':'Deck do BOT')+' deck foi embaralhado pelo OCGCore.')}else if(msg===33){var hp=dv.getUint8(1),hand=hp===0?state.playerHand:state.botHand;shuffleMirrorArray(hand);render()}else if(msg===50){mirrorMovePacket(pkt)}`);

    source=source.replace(`passChainBtn.onclick=function(){\n  if(real.pending&&real.pending.msg===16&&!real.pending.forced){respondInt(-1);real.pending=null;updatePromptUI();pumpReal()}\n};`,`var shuffleDeckBtn=document.createElement('button');shuffleDeckBtn.type='button';shuffleDeckBtn.textContent='SHUFFLE DECK';shuffleDeckBtn.hidden=true;shuffleDeckBtn.className='secondary';if(passChainBtn&&passChainBtn.parentNode)passChainBtn.parentNode.insertBefore(shuffleDeckBtn,passChainBtn.nextSibling);shuffleDeckBtn.onclick=function(){if(real.pending&&real.pending.msg===11&&real.pending.player===0&&real.pending.shuffle){respondInt(8);real.pending=null;updatePromptUI();pumpReal()}};passChainBtn.onclick=function(){if(real.pending&&real.pending.msg===16&&!real.pending.forced){respondInt(-1);real.pending=null;updatePromptUI();pumpReal()}};`);

    source=source.replace("passChainBtn.hidden=true;",`passChainBtn.hidden=true;if(typeof shuffleDeckBtn!=='undefined')shuffleDeckBtn.hidden=!(p&&p.msg===11&&p.player===0&&p.shuffle);var ep=$('#playerExtraPile');if(ep){var extraLegal=!!(p&&p.player===0&&p.msg===11&&(p.special||[]).some(function(x){return Number(x.location)===64}));ep.classList.toggle('legal-active',extraLegal);}`);

    source=source.replace("var startRealBtn=$('#startRealBtn');if(startRealBtn)startRealBtn.onclick=startRealDuel;",`document.querySelectorAll('#phaseBar button').forEach(function(btn){btn.onclick=function(){if(!real.active||!real.pending||real.pending.player!==0)return;var ph=btn.dataset.phase,p=real.pending;if(p.msg===11){if(ph==='BP'&&p.toBP){respondInt(6);real.pending=null;updatePromptUI();pumpReal()}else if(ph==='EP'&&p.toEP){respondInt(7);real.pending=null;updatePromptUI();pumpReal()}}else if(p.msg===10){if(ph==='M2'&&p.toM2){respondInt(2);real.pending=null;updatePromptUI();pumpReal()}else if(ph==='EP'&&p.toEP){respondInt(3);real.pending=null;updatePromptUI();pumpReal()}}}});var startRealBtn=$('#startRealBtn');if(startRealBtn)startRealBtn.onclick=startRealDuel;`);

    const style=document.createElement('style');style.textContent='#playerExtraPile.legal-active{outline:2px solid #4fd8ff;box-shadow:0 0 18px rgba(79,216,255,.55)}';document.head.appendChild(style);
    new Function(source+'\n//# sourceURL=duellab-runtime.js')();
  }catch(error){console.error(error);if(status)status.textContent='Erro ao carregar Duel Lab: '+(error.message||error)}
})();