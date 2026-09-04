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

    // O banco possuia aliases/baseId que podiam sobrescrever o ID real de outra
    // carta. Isso fazia o core comprar um codigo correto e a interface exibir,
    // por engano, uma carta do Extra Deck. IDs exatos agora sempre vencem.
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

    // MSG_DRAW atual: player(u8), count(u32), seguido por code(u32)+position(u32).
    source=source.replace(
      "for(var d=0;d<n&&o2+4<=pkt.length;d++){codes.push(u32(dv,o2));o2+=4}",
      "for(var d=0;d<n&&o2+8<=pkt.length;d++){codes.push(u32(dv,o2));o2+=8}"
    );

    // Protecao adicional do espelho visual: uma compra nunca deve retirar uma
    // carta do Extra. Se um codigo reportado nao existir no Main restante mas
    // existir no Extra, mantemos a mao sincronizada com o topo do Main e avisamos
    // no console, sem alterar o estado interno do OCGCore.
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

    // MZONE possui 7 sequencias (5 principais + 2 EMZ) e SZONE suporta
    // sequencias adicionais para Field/Pendulum conforme o core.
    source=source.replace(
      "var slot=(seq!=null&&seq>=0&&seq<5)?seq:pool.findIndex(function(x){return !x});",
      "var zoneLimit=loc===4?7:8;var slot=(seq!=null&&seq>=0&&seq<zoneLimit)?seq:pool.findIndex(function(x){return !x});"
    );

    // Bibliotecas/procedures atuais do CardScripts usadas pelo EDOPro.
    source=source.replace(
      "'proc_workaround.lua'\n];",
      "'proc_workaround.lua','proc_persistent.lua','proc_rush.lua','proc_skill.lua'\n];"
    );

    // Campo moderno: 5 MMZ, 2 EMZ compartilhadas, 5 S/T, Pendulum nas pontas
    // e Field Zone separada. Mantem os mesmos indices usados pelo OCGCore.
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

    // Os botoes de fase agora respondem ao mesmo prompt do OCGCore usado pelos
    // comandos do EDOPro: BP/EP na Main Phase e M2/EP na Battle Phase.
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