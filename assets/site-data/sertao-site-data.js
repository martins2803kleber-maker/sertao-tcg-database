(function(){
'use strict';
if(window.__SERTAO_SITE_DATA_INSTALLED__)return;
window.__SERTAO_SITE_DATA_INSTALLED__=true;

var nativeFetch=window.fetch&&window.fetch.bind(window);
if(!nativeFetch)return;
var CDN='https://cdn.jsdelivr.net/gh/martins2803kleber-maker/sertao-tcg-database@main/data/site/';
var exact=/^https:\/\/(?:raw\.githubusercontent\.com\/martins2803kleber-maker\/sertao-tcg-database\/main|cdn\.jsdelivr\.net\/gh\/martins2803kleber-maker\/sertao-tcg-database@(?:main|[A-Fa-f0-9]+))\/data\/(yugioh|onepiece)\.json(?:\?.*)?$/;

function sourceUrl(input){return typeof input==='string'?input:(input&&input.url)||'';}
function cloneInit(init){var out={};if(init)Object.keys(init).forEach(function(k){out[k]=init[k];});out.cache='force-cache';return out;}

window.fetch=function(input,init){
  var url=sourceUrl(input),m=url.match(exact);
  if(!m||window.__SERTAO_SITE_DATA_DISABLE__)return nativeFetch(input,init);
  var compact=CDN+m[1]+'.json';
  return nativeFetch(compact,cloneInit(init)).then(function(resp){
    if(resp&&resp.ok)return resp;
    return nativeFetch(input,init);
  }).catch(function(err){
    if(init&&init.signal&&init.signal.aborted)throw err;
    return nativeFetch(input,init);
  });
};

window.SertaoTCGSiteData={
  version:'2.1',
  compactBase:CDN,
  originalFetch:nativeFetch,
  restore:function(){window.fetch=nativeFetch;window.__SERTAO_SITE_DATA_DISABLE__=true;}
};
})();
