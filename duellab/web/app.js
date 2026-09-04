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

    // Cloudflare serves duellab/web as the site root. The OCGCore/WASM and
    // core data live outside that directory in the repository, so relative
    // ../../assets URLs cannot exist in the deployed static site. Load those
    // versioned public assets from the repository CDN instead.
    source=source.replace(
      "var REAL_BASE='../../assets/duellab/';",
      "var REAL_BASE='https://cdn.jsdelivr.net/gh/martins2803kleber-maker/sertao-tcg-database@main/assets/duellab/';"
    );

    new Function(source+'\n//# sourceURL=duellab-runtime.js')();
  }catch(error){
    console.error(error);
    if(status)status.textContent='Erro ao carregar Duel Lab: '+(error.message||error);
  }
})();
