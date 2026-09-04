(async function(){
  const status=document.querySelector('#engineStatus');
  const files=['01.txt','02.txt','03.txt','04.txt','05.txt','06.txt'];
  try{
    let source='';
    for(let i=0;i<files.length;i++){
      const file=files[i];
      if(status)status.textContent='Carregando Duel Lab '+(i+1)+'/'+files.length+'...';
      const response=await fetch('./chunks/'+file,{cache:'no-cache'});
      if(!response.ok)throw new Error(file+' HTTP '+response.status);
      source+=await response.text();
    }

    // Cloudflare publica apenas duellab/web. O motor fica fora dessa raiz,
    // portanto usamos uma revisao fixa via jsDelivr para JS/WASM/core data.
    source=source.replace(
      "var REAL_BASE='../../assets/duellab/';",
      "var REAL_BASE='https://cdn.jsdelivr.net/gh/martins2803kleber-maker/sertao-tcg-database@6d321c117c77f000a78274fb8c72c1a727f9533c/assets/duellab/';"
    );

    // IDs reais do banco sempre vencem aliases/baseId/originalId.
    source=source.replace(
`      state.byId=new Map();
      data.forEach(function(c){
        [c.id,c.baseId,c.originalId].filter(Boolean).forEach(function(id){state.byId.set(String(id),c)});
      });`,
`      state.byId=new Map();
      data.forEach(function(c){
        if(c && c.id!=null)state.byId.set(String(c.id),c);
      });
      data.forEach(function(c){
        [c.baseId,c.originalId].filter(Boolean).forEach(function(id){
          var key=String(id);if(!state.byId.has(key))state.byId.set(key,c);
        });
      });`
    );

    // MSG_DRAW: code(u32)+position(u32) por carta.
    source=source.replace(
      "for(var d=0;d<n&&o2+4<=pkt.length;d++){codes.push(u32(dv,o2));o2+=4}",
      "for(var d=0;d<n&&o2+8<=pkt.length;d++){codes.push(u32(dv,o2));o2+=8}"
    );

    source=source.replace(
`function mirrorDraw(side,codes){
  var hand=side===0?state.playerHand:state.botHand;
  var deck=side===0?state.playerDeck:state.botDeck;
  codes.forEach(function(code){
    var ix=deck.findIndex(function(c){return Number(c.id||c.baseId||c.originalId)===Number(code)});
    var card=ix>=0?deck.splice(ix,1)[0]:cardByCode(code);
    hand.push(card);
  });
  render();
}`,
`function mirrorDraw(side,codes){
  var hand=side===0?state.playerHand:state.botHand;
  var deck=side===0?state.playerDeck:state.botDeck;
  var extra=side===0?state.playerExtra:state.botExtra;
  codes.forEach(function(code){
    var ix=deck.findIndex(function(c){return Number(c&&c.id)===Number(code)});
    var inExtra=(extra||[]).some(function(c){return Number(c&&c.id)===Number(code)});
    var card;
    if(ix>=0)card=deck.splice(ix,1)[0];
    else if(inExtra && deck.length){
      console.warn('Duel Lab: MSG_DRAW apontou codigo do Extra; espelho manteve compra no Main Deck.',code);
      card=deck.shift();
    }else card=cardByCode(code);
    hand.push(card);
  });
  render();
}`
    );

    source=source.replace(
      "var slot=(seq!=null&&seq>=0&&seq<5)?seq:pool.findIndex(function(x){return !x});",
      "var zoneLimit=loc===4?7:8;var slot=(seq!=null&&seq>=0&&seq<zoneLimit)?seq:pool.findIndex(function(x){return !x});"
    );

    source=source.replace(
      "'proc_workaround.lua'\n];",
      "'proc_workaround.lua','proc_persistent.lua','proc_rush.lua','proc_skill.lua'\n];"
    );

    // O protocolo moderno usado pelo EDOPro/OCGCore usa count e sequence de
    // 1 byte nos grupos de MSG_SELECT_IDLECMD. A versao anterior lia u32,
    // desalinhava o pacote e fazia o menu concluir que nenhuma carta era legal.
    source=source.replace(
      /function parseIdle\(pkt\)\{[\s\S]*?\n\}\nfunction parseBattle\(pkt\)\{/,
`function parseIdle(pkt){
  var dv=new DataView(pkt.buffer,pkt.byteOffset,pkt.byteLength),o=1;
  var player=dv.getUint8(o++),groups=[];
  function cards(activate){
    var n=dv.getUint8(o++),a=[];
    for(var i=0;i<n;i++){
      var c=readCardRef(dv,o,false);o=c.next;
      if(activate){c.description=u64num(dv,o);o+=8;c.clientMode=dv.getUint8(o++)}
      a.push(c);
    }
    return a;
  }
  groups.push(cards(false));
  groups.push(cards(false));
  groups.push(cards(false));
  groups.push(cards(false));
  groups.push(cards(false));
  groups.push(cards(true));
  var out={msg:11,player:player,summon:groups[0],special:groups[1],reposition:groups[2],mset:groups[3],sset:groups[4],activate:groups[5],toBP:!!dv.getUint8(o++),toEP:!!dv.getUint8(o++),shuffle:!!dv.getUint8(o++)};
  console.debug('Duel Lab SELECT_IDLECMD',out);
  return out;
}
function parseBattle(pkt){`
    );

    // MSG_SELECT_BATTLECMD segue o mesmo formato compacto de count/sequence.
    source=source.replace(
      /function parseBattle\(pkt\)\{[\s\S]*?\n\}\n\nfunction parseChain\(pkt\)\{/,
`function parseBattle(pkt){
  var dv=new DataView(pkt.buffer,pkt.byteOffset,pkt.byteLength),o=1,player=dv.getUint8(o++);
  var na=dv.getUint8(o++),act=[];
  for(var i=0;i<na;i++){
    var c=readCardRef(dv,o,false);o=c.next;
    c.description=u64num(dv,o);o+=8;c.clientMode=dv.getUint8(o++);act.push(c);
  }
  var nb=dv.getUint8(o++),atklist=[];
  for(var j=0;j<nb;j++){
    var c2=readCardRef(dv,o,false);o=c2.next;
    c2.direct=!!dv.getUint8(o++);atklist.push(c2);
  }
  return {msg:10,player:player,activate:act,attack:atklist,toM2:!!dv.getUint8(o++),toEP:!!dv.getUint8(o++)};
}

function parseChain(pkt){`
    );

    // Campo moderno: 5 MMZ, 2 EMZ compartilhadas, 5 S/T, P-Zones e Field.
    source=source.replace(
      /function renderField\(id,cards,label,side\)\{[\s\S]*?\n\}\nfunction renderSpell\(id,cards,side\)\{[\s\S]*?\n\}\nfunction render\(\)\{/,
`function runtimeZoneHtml(c,label,side,location,sequence,extraClass){
  extraClass=extraClass||'';
  if(!c)return '<div class="stdl-zone '+extraClass+'" data-side="'+side+'" data-location="'+location+'" data-sequence="'+sequence+'"><span class="stdl-zone-label">'+label+'</span></div>';
  var html=zoneHtml(c,label);
  html=html.replace('class="stdl-zone monster occupied"','class="stdl-zone monster occupied '+extraClass+'" data-side="'+side+'" data-location="'+location+'" data-sequence="'+sequence+'"');
  return html;
}
function renderField(id,cards,label,side){
  cards=cards||[];var h='';
  for(var i=0;i<5;i++)h+=runtimeZoneHtml(cards[i],label,side,4,i,'stdl-main-monster-zone');
  $(id).innerHTML=h;
}
function renderSpell(id,cards,side){
  cards=cards||[];var h='';
  for(var i=0;i<5;i++){
    var sourceSeq=i,c=cards[i];
    if(!c&&i===0&&cards[6]){c=cards[6];sourceSeq=6}
    if(!c&&i===4&&cards[7]){c=cards[7];sourceSeq=7}
    var cls='stdl-spell-zone'+(i===0?' stdl-pzone-left':i===4?' stdl-pzone-right':'');
    h+=runtimeZoneHtml(c,(i===0||i===4)?'P / S-T':'S/T',side,8,sourceSeq,cls);
  }
  $(id).innerHTML=h;
}
function renderFieldSideZone(id,cards,side){
  var el=$(id);if(!el)return;cards=cards||[];
  el.innerHTML=runtimeZoneHtml(cards[5],'FIELD',side,8,5,'stdl-field-zone-inner');
}
function renderExtraMonsterZones(){
  var left=$('#extraMonsterZoneLeft'),right=$('#extraMonsterZoneRight');if(!left||!right)return;
  var lc=state.playerField[5]||state.botField[6],ls=state.playerField[5]?0:(state.botField[6]?1:0),lseq=state.playerField[5]?5:6;
  var rc=state.playerField[6]||state.botField[5],rs=state.playerField[6]?0:(state.botField[5]?1:0),rseq=state.playerField[6]?6:5;
  left.outerHTML=runtimeZoneHtml(lc,'EMZ',ls,4,lseq,'stdl-emz-zone').replace('<div ','<div id="extraMonsterZoneLeft" ');
  right.outerHTML=runtimeZoneHtml(rc,'EMZ',rs,4,rseq,'stdl-emz-zone').replace('<div ','<div id="extraMonsterZoneRight" ');
}
function render(){`
    );

    source=source.replace(
      "renderSpell('#botSpell',state.botSpellField,'1');renderField('#botMonsters',state.botField,'MONSTER','1');\n  renderField('#playerMonsters',state.playerField,'MONSTER','0');renderSpell('#playerSpell',state.playerSpellField,'0');",
      "renderSpell('#botSpell',state.botSpellField,'1');renderField('#botMonsters',state.botField,'MONSTER','1');\n  renderExtraMonsterZones();renderFieldSideZone('#botFieldZone',state.botSpellField,'1');\n  renderField('#playerMonsters',state.playerField,'MONSTER','0');renderSpell('#playerSpell',state.playerSpellField,'0');renderFieldSideZone('#playerFieldZone',state.playerSpellField,'0');"
    );

    source=source.replace(
      "var startRealBtn=$('#startRealBtn');if(startRealBtn)startRealBtn.onclick=startRealDuel;",
`document.querySelectorAll('#phaseBar button').forEach(function(btn){
  btn.onclick=function(){
    if(!real.active||!real.pending||real.pending.player!==0)return;
    var phase=btn.dataset.phase,p=real.pending;
    if(p.msg===11){
      if(phase==='BP'&&p.toBP){respondInt(6);real.pending=null;updatePromptUI();pumpReal();}
      else if(phase==='EP'&&p.toEP){respondInt(7);real.pending=null;updatePromptUI();pumpReal();}
    }else if(p.msg===10){
      if(phase==='M2'&&p.toM2){respondInt(2);real.pending=null;updatePromptUI();pumpReal();}
      else if(phase==='EP'&&p.toEP){respondInt(3);real.pending=null;updatePromptUI();pumpReal();}
    }
  };
});
var startRealBtn=$('#startRealBtn');if(startRealBtn)startRealBtn.onclick=startRealDuel;`
    );

    new Function(source+'\n//# sourceURL=duellab-runtime.js')();
  }catch(error){
    console.error(error);
    if(status)status.textContent='Erro ao carregar Duel Lab: '+(error.message||error);
  }
})();