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
    // portanto usamos uma revisão fixa via jsDelivr para JS/WASM/core data.
    source=source.replace(
      "var REAL_BASE='../../assets/duellab/';",
      "var REAL_BASE='https://cdn.jsdelivr.net/gh/martins2803kleber-maker/sertao-tcg-database@6d321c117c77f000a78274fb8c72c1a727f9533c/assets/duellab/';"
    );

    // O protocolo MSG_DRAW atual do OCGCore envia 8 bytes por carta:
    // code (u32) + position (u32). A versão anterior avançava somente 4 bytes,
    // interpretando posição como ID de carta e misturando cartas do Extra na mão.
    source=source.replace(
      "for(var d=0;d<n&&o2+4<=pkt.length;d++){codes.push(u32(dv,o2));o2+=4}",
      "for(var d=0;d<n&&o2+8<=pkt.length;d++){codes.push(u32(dv,o2));o2+=8}"
    );

    // MZONE possui 7 sequências (5 principais + 2 EMZ) e SZONE suporta
    // sequências adicionais para Field/Pendulum conforme a regra usada pelo core.
    source=source.replace(
      "var slot=(seq!=null&&seq>=0&&seq<5)?seq:pool.findIndex(function(x){return !x});",
      "var zoneLimit=loc===4?7:8;var slot=(seq!=null&&seq>=0&&seq<zoneLimit)?seq:pool.findIndex(function(x){return !x});"
    );

    // Troca a renderização simplificada de 7 colunas por uma representação do
    // campo moderno: 5 MMZ, duas EMZ compartilhadas, 5 S/T, P-Zones nas pontas
    // e Field Zone separada. Mantém os mesmos IDs/ações do OCGCore.
    source=source.replace(
      /function renderField\(id,cards,label,side\)\{[\s\S]*?\n\}\nfunction renderSpell\(id,cards,side\)\{[\s\S]*?\n\}\nfunction render\(\)\{/,
`function runtimeZoneHtml(c,label,side,location,sequence,extraClass){
  extraClass=extraClass||'';
  if(!c)return '<div class="stdl-zone '+extraClass+'"><span class="stdl-zone-label">'+label+'</span></div>';
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

    new Function(source+'\n//# sourceURL=duellab-runtime.js')();
  }catch(error){
    console.error(error);
    if(status)status.textContent='Erro ao carregar Duel Lab: '+(error.message||error);
  }
})();
