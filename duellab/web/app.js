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
    new Function(source+'\n//# sourceURL=duellab-runtime.js')();
  }catch(error){
    console.error(error);
    if(status)status.textContent='Erro ao carregar Duel Lab: '+(error.message||error);
  }
})();
