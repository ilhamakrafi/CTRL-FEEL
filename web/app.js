const form = document.querySelector('#analyze-form');
const text = document.querySelector('#text');
const status = document.querySelector('#status');
const submit = document.querySelector('#submit');
const output = document.querySelector('#output');
const empty = document.querySelector('#empty');
let lastResult = null;
let request = null;
let revision = 0;
const actionNames = {ask_clarification:'Demander une précision',acknowledge:'Accuser réception du message',offer_help:'Proposer de l’aide',respect_boundary:'Respecter la demande d’arrêt'};
const reactionNames = {rejects_help:'Seuils d’activation et de dominance élevés',stays_negative:'Seuil de valence bas',opens_up:'Autre combinaison de scores'};
const sourceNames = {csv:'Action trouvée dans la table CSV.',fallback_missing_csv:'Table CSV absente : demande de précision par défaut.',fallback_no_match:'Aucune correspondance dans le CSV : demande de précision par défaut.',fallback_unsupported_action:'Action CSV non prise en charge : demande de précision par défaut.'};
function resetResult(){ lastResult = null; output.hidden = true; empty.hidden = false; document.querySelector('#result-tag').textContent = 'EN ATTENTE'; }
function count(){ document.querySelector('#count').textContent = `${text.value.length} / 2000`; }
function changed(){ revision++; request?.abort(); submit.disabled=false; resetResult(); count(); status.textContent='Texte ou action modifié. Lancez une nouvelle analyse.'; }
text.addEventListener('input',changed);
document.querySelector('#action').addEventListener('change',changed);
document.querySelectorAll('[data-example]').forEach(button=>button.addEventListener('click',()=>{text.value=button.dataset.example;changed();text.focus();}));
form.addEventListener('submit',async event=>{
  event.preventDefault();
  if(!text.value.trim()){status.textContent='Saisissez un texte en anglais.';return;}
  request?.abort(); request=new AbortController(); const current=++revision;
  resetResult(); submit.disabled=true; status.textContent='Analyse en cours. Le premier chargement du modèle peut prendre du temps.';
  try{
    const response=await fetch('/api/analyze',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({user_text:text.value,current_system_action:document.querySelector('#action').value}),signal:request.signal});
    const data=await response.json(); if(current!==revision)return;
    if(!response.ok)throw new Error(data.error || 'Analyse indisponible.');
    lastResult=data;
    for(const key of ['valence','arousal','dominance'])document.getElementById(key).textContent=Number(data.vad_scores[key]).toFixed(3);
    document.querySelector('#reaction').textContent=reactionNames[data.mapped_vad_state] || data.mapped_vad_state;
    document.querySelector('#method').textContent=data.method_note;
    document.querySelector('#next-action').textContent=actionNames[data.next_system_action] || data.next_system_action;
    document.querySelector('#decision-source').textContent=sourceNames[data.decision_source] || data.decision_source;
    document.querySelector('#result-tag').textContent='ANALYSE TERMINÉE';
    empty.hidden=true;output.hidden=false;status.textContent='Analyse terminée. Le texte n’a pas été enregistré.';
  }catch(error){if(error.name!=='AbortError' && current===revision)status.textContent=error.message;}
  finally{if(current===revision)submit.disabled=false;}
});
document.querySelector('#clear').addEventListener('click',()=>{revision++;request?.abort();form.reset();submit.disabled=false;resetResult();count();status.textContent='Session effacée.';text.focus();});
document.querySelector('#download').addEventListener('click',()=>{if(!lastResult)return;const url=URL.createObjectURL(new Blob([JSON.stringify(lastResult,null,2)],{type:'application/json'}));const link=document.createElement('a');link.href=url;link.download='ctrl-feel-resultat.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
fetch('/api/status').then(response=>response.json()).then(data=>{document.querySelector('#csv-status').textContent=data.csv_available?'La table My_Aggregated_Logic.csv est présente. Ses colonnes seront vérifiées lors de l’analyse.':'Le fichier My_Aggregated_Logic.csv est absent. L’analyse reste disponible avec une demande de précision par défaut.';}).catch(()=>{document.querySelector('#csv-status').textContent='État de la table indisponible. Vérifiez que le serveur local est lancé.';});
