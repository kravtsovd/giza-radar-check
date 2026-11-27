'use strict';
const pagesBase='https://kravtsovd.github.io/giza-radar-check/';
const repository='https://github.com/kravtsovd/giza-radar-check';
const q=(s,el=document)=>el.querySelector(s);
const qa=(s,el=document)=>Array.from(el.querySelectorAll(s));
let data=JSON.parse(q('#snapshot').textContent);
let lang=new URLSearchParams(location.search).get('lang')==='ru'?'ru':'en';
const tr=(en,ru)=>lang==='ru'?ru:en;
const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const anchor=(section,id)=>'#'+section+(id?'/'+encodeURIComponent(id):'');
const field=(r,k)=>{const v=(lang==='ru'&&(r['ru_'+k]||r[k+'_ru']||(k==='title'&&r.ru)))||r[k]||'';return typeof v==='string'?v:Array.isArray(v)?v.join(' · '):''};
function href(x) {
 if(typeof x!=='string'||!x)return '';
 try {const u=new URL(x,pagesBase);return u.protocol==='https:'?u.href:''}catch{return ''}
}
function link(text,url){const dest=href(url);return dest?'<a href="'+esc(dest)+'">'+esc(text)+'</a>':''}
function innerLink(text,section,id){return '<a href="'+esc(anchor(section,id))+'">'+esc(text)+'</a>'}
const stageStatus={inputs:['Measured','Данные получены'],looks:['Implemented','Реализовано'],track:['Tested','Проверено'],steer:['Scale unresolved','Масштаб неизвестен'],focus:['36 variants tested','Проверены 36 вариантов'],shape:['Shape test failed','Форма не воспроизвелась'],validate:['Partial transfer','Частичная повторяемость']};
const overrides={
 lead:'Может ли спутниковый радар найти известную камеру? Мы сверяем прогнозы с обмерами, прежде чем судить о восьми предполагаемых шахтах под Хефреном.',
 status:'Что показали проверки',motion:'Движение поверхности',motionResult:'На вибраторе спутник показал 2,01 Гц. Датчик на земле измерил 2,00 Гц.',openTest:'Проверка частоты',
 chamber:'Известная камера',chamberResult:'При заданной высоте камера царя прошла порог на 2 из 5 проверочных снимков. Свободный поиск высоты ошибся на всех 6.',
 sixScenes:'Шесть съёмок',shafts:'Восемь шахт',shaftsResult:'648 м получили из масштаба рисунка в презентации. Независимого измерения глубины пока нет.',depthCheck:'Проверка глубины',
 trace:'Как проверили камеру царя',map:'Открыть карту решений',film:'Смотреть фильм проекта',browse:'Открыть библиотеку',contrib:'Как добавить материал',error:'Сообщить об ошибке'
};
const pageNames={overview:['Overview','Обзор'],method:['Algorithm','Алгоритм'],datasets:['Data','Данные'],tests:['Tests & decisions','Проверки и решения'],library:['Library','Материалы']};
const original=new Map(qa('[data-copy]').map(e=>[e,e.textContent]));
let tables={};
function recordList(kind){return kind==='library'?[...data.library.items,...fileRows()]:data.datasets.items}
function fileRows(){
 return data.files.map(f=>({id:'file-'+f.path,group:tr('Project files','Файлы проекта'),title:f.path,access:tr('Public','Открыто'),url:repository+'/blob/main/'+f.path.split('/').map(encodeURIComponent).join('/'),description:tr('Public repository file.','Файл из публичного репозитория.')}));
}
function resultsByWord(...words){return data.research.tests.find(r=>words.some(w=>r.id.includes(w)))}
function jumpTests(){
 return {six:resultsByWord('six-scene','king-transfer','king-location','transfer-king','chamber-transfer','held-out'),surface:resultsByWord('driven-motion','centroid','surface-motion','shaker'),depth:resultsByWord('depth-scale','scale-depth','648','depth')};
}
function overview(){
 const j=jumpTests();
 for(const e of qa('[data-jump]')){const t=j[e.dataset.jump];e.href=anchor('tests',t?.id)}
 q('[data-map]').href=pagesBase+'decision-map.html?lang='+lang;
 const test=j.six;
 const stage=data.research.stages.find(s=>(test?.stage_ids||[]).includes(s.id))||data.research.stages[0];
 const e=q('#next-decision');
 if(e){e.innerHTML='<summary>'+esc(tr('What would change the conclusion?','Какая проверка изменит вывод?'))+'</summary><p>'+esc(field(data.research.next_test,'rule'))+'</p>'}
 q('#chain').innerHTML=[innerLink(tr('Claim and source','Тезис и источник'),'library',(data.library.items.find(r=>r.url?.includes('SjJTRVgr9Mw'))||{}).id),innerLink(tr('16 Sep · Capella','16 сен · Capella'),'datasets','capella-20240916'),innerLink(tr('Processing stage','Стадия обработки'),'method',stage?.id),innerLink(tr('Frozen test and verdict','Проверка и решение'),'tests',test?.id)].join('<span aria-hidden="true">→</span>');
}
function sectionHead(title,desc){return '<h2>'+esc(title)+'</h2><p class="intro">'+esc(desc)+'</p>'}
function detailCell(label,value){return value?'<div><span class="label">'+esc(label)+'</span>'+esc(value)+'</div>':''}
function sourceLinks(r) {
 let urls=[r.url,...(r.sources||[])].map(s=>typeof s==='string'?s:s?.url).filter(x=>href(x));
 return [...new Set(urls)].map((u,i)=>link(tr('Source','Источник')+' '+(i+1),u)).join(' ');
}
function renderMethod(){
 const {stages}=data.research;
 q('#method').innerHTML=sectionHead(tr('From radar echoes to a proposed depth','От радиолокационного эха к предполагаемой глубине'),tr('Open a stage to see what the authors described, what we tried and which choices remain unknown.','Откройте стадию, чтобы увидеть слова авторов, проведённую проверку и недостающие параметры.'))+
 '<div class="math">'+esc(tr('36 variants = 3 pairings × 2 geometries × 3 wavelengths × 2 scoring rules','36 вариантов = 3 способа выбора пар × 2 геометрии × 3 длины волны × 2 способа оценки'))+'</div><div class="flow">'+stages.map(s=>'<a href="'+esc(anchor('method',s.id))+'"><span>'+esc(field(s,'title'))+'<small>'+esc(tr(...(stageStatus[s.id]||['Open stage','Открыть стадию'])))+'</small></span></a>').join('<i aria-hidden="true">→</i>')+'</div>'+
 stages.map(s=>'<details class="node" data-rid="'+esc(s.id)+'"><summary>'+esc(field(s,'title'))+'</summary><div class="detailbody">'+detailCell(tr('Published description','Что известно'),field(s,'known'))+detailCell(tr('Tested here','Что мы проверили'),field(s,'test'))+detailCell(tr('Unknown or assumed','Что остаётся неизвестным'),field(s,'unknown'))+'</div><div class="links">'+data.research.tests.filter(t=>t.stage_ids?.includes(s.id)).map(t=>innerLink(field(t,'title'),'tests',t.id)).join(' ')+sourceLinks(s)+'</div></details>').join('');
}
function candidateGrid(){
 const f=data.research.candidate_family;
 if(!f?.variants?.length)return;
 const box=document.createElement('details');box.className='node';
 box.innerHTML='<summary>'+tr('Explore the 36 tested combinations','Посмотреть 36 проверенных комбинаций')+'</summary><p>'+tr('Choose how to pair looks, model geometry, set wavelength and score. The cells show how many of 32 neighbors the supplied King’s Chamber position beat. Only September was used for selection.','Выберите пары, геометрию, длину волны и способ оценки. Числа показывают, сколько из 32 соседей обошла заданная точка камеры царя. Настройки подбирали только по сентябрю.')+'</p><div class="controls"></div><p class="math" aria-live="polite"></p>';
 const fields=[['pairing',tr('Pairing','Пары')],['geometry',tr('Geometry','Геометрия')],['wavelength_m',tr('Wavelength, m','Длина волны, м')],['estimator',tr('Score','Оценка')]];
 const selected=f.variants.find(v=>v.selected)||f.variants[0];
 for(const [key,title] of fields){const label=document.createElement('label');label.textContent=title+' ';const select=document.createElement('select');select.dataset.key=key;for(const val of [...new Set(f.variants.map(v=>String(v[key])))])select.add(new Option(val,val));select.value=String(selected[key]);select.onchange=update;label.append(select);q('.controls',box).append(label)}
 function update(){const picks=qa('select',box);const v=f.variants.find(v=>picks.every(p=>String(v[p.dataset.key])===p.value));q('.math',box).textContent=Object.entries(v.ranks_against_32).map(([k,r])=>k+' · '+r.King+'/32').join('  |  ')+(v.selected?' · '+tr('training winner','выбрано на обучении'):'')}
 update();q('#method').append(box)
}

function renderTests(){
 const ds=new Map(data.datasets.items.map(r=>[r.id,r]));
 const st=new Map(data.research.stages.map(r=>[r.id,r]));
 q('#tests').innerHTML=sectionHead(tr('Tests and decisions','Проверки и решения'),tr('Each record connects a claim with its input, result, limits and the decision it supports.','В каждой записи тезис связан с исходными данными, результатом, ограничениями и решением.'))+
 data.research.tests.map(t=>'<details class="node" data-rid="'+esc(t.id)+'"><summary>'+esc(field(t,'title'))+'</summary><div class="detailbody">'+detailCell(tr('Claim','Проверяемый тезис'),field(t,'claim'))+detailCell(tr('Observation','Что получили'),field(t,'result'))+detailCell(tr('Decision','Решение'),field(t,'decision'))+detailCell(tr('Next test','Следующая проверка'),field(t,'next_test'))+'</div><div class="links">'+(t.stage_ids||[]).filter(k=>st.has(k)).map(k=>innerLink(field(st.get(k),'title'),'method',k)).join(' ')+(t.scene_ids||[]).filter(k=>ds.has(k)).map(k=>innerLink(field(ds.get(k),'title'),'datasets',k)).join(' ')+(t.evidence_ids||[]).map(id=>data.research.independent_evidence.find(e=>e.id===id)).filter(Boolean).map(e=>link(e.title,e.url)).join(' ')+sourceLinks(t)+'</div></details>').join('');
}
function columnDefs(kind){return kind==='datasets'?[['title',tr('Dataset / source','Набор / источник')],['date',tr('Date (UTC)','Дата (UTC)')],['platform',tr('Platform','Платформа')],['product',tr('Product','Продукт')],['access',tr('Access','Доступ')]]:[['title',tr('Title / source','Название / источник')],['group',tr('Collection','Раздел')],['access',tr('Access','Доступ')]]}
function tableShell(kind){
 const cols=columnDefs(kind);
 const h=kind==='datasets'?sectionHead(tr('Satellite scenes and ground surveys','Спутниковые съёмки и наземные обмеры'),tr('Dates refer to acquisition when known. Open an entry for the site, product, access conditions and use in a test.','Для снимков указана дата съёмки, если она известна. В записи есть место, продукт, доступ и его роль в проверке.')):sectionHead(tr('Project library','Библиотека проекта'),tr('Interviews, articles, time-stamped statements, code, films and public working files. Restricted collections carry an access label.','Интервью, статьи, утверждения с таймкодами, код, фильмы и открытые файлы проекта. Для закрытых коллекций указан режим доступа.'));
 q('#'+kind).innerHTML=h+'<div class="controls"><input type="search" class="search" aria-label="Search all fields" placeholder="'+esc(tr('Search all fields','Искать по всем полям'))+'"><button class="expand"></button><button class="reset">'+tr('Reset filters','Сбросить фильтры')+'</button><small class="filecount" aria-live="polite"></small></div><div class="table-scroll"><table><thead><tr><th><button data-sort="count">'+tr('Count','Число')+'</button></th>'+cols.map(([k,label])=>'<th><button data-sort="'+k+'">'+label+'</button></th>').join('')+'</tr><tr class="filters"><td></td>'+cols.map(([k,label])=>'<td><input data-filter="'+k+'" aria-label="'+esc(tr('Filter ','Фильтр ')+label)+'"></td>').join('')+'</tr></thead><tbody></tbody></table></div>';
 const section=q('#'+kind),state=tables[kind];
 const coverage=document.createElement('details');coverage.className='scope';
 coverage.innerHTML='<summary>'+esc(tr('Catalog coverage','Охват каталога'))+'</summary><p>'+esc(data[kind].scope||'')+'</p>';section.append(coverage);
 q('.search',section).value=state.search;
 for(const e of qa('[data-filter]',section)){e.value=state.filters[e.dataset.filter]||'';e.oninput=()=>{state.filters[e.dataset.filter]=e.value;state.closedSearch=false;fillTable(kind)}}
 q('.search',section).oninput=e=>{state.search=e.target.value;state.closedSearch=false;fillTable(kind)};
 q('.reset',section).onclick=()=>{tables[kind]=fresh();tableShell(kind)};
 q('.expand',section).onclick=()=>{const opened=state.expandAll||state.forceOpen;state.expandAll=!opened;state.forceOpen=false;state.closedSearch=opened;state.opens.clear();fillTable(kind)};
 for(const e of qa('[data-sort]',section))e.onclick=()=>{const k=e.dataset.sort;state.dir=k===state.sort?-state.dir:(k==='count'?-1:1);state.sort=k;fillTable(kind)};
 fillTable(kind);
}
function fresh(){return {search:'',filters:{},sort:'count',dir:-1,expandAll:false,forceOpen:false,closedSearch:false,opens:new Set(),target:null}}
function fillTable(kind){
 const section=q('#'+kind),state=tables[kind],cols=columnDefs(kind),rows=recordList(kind),str=(r,k)=>field(r,k).toLocaleLowerCase();
 const filter=r=>cols.every(([k])=>str(r,k).includes((state.filters[k]||'').toLocaleLowerCase()))&&[...cols.map(x=>x[0]),'description','site','related','id','url','source_id','rights'].some(k=>str(r,k).includes(state.search.toLocaleLowerCase()));
 const groups=new Map();
 for(const r of rows.filter(filter)){const g=field(r,'group')||tr('Records','Записи');if(!groups.has(g))groups.set(g,[]);groups.get(g).push(r)}
 const hasFilter=Boolean(state.search||Object.values(state.filters).some(Boolean));state.forceOpen=hasFilter&&!state.closedSearch;
 q('.expand',section).textContent=state.expandAll||state.forceOpen?tr('Collapse all','Свернуть все'):tr('Expand all','Раскрыть все');
 q('.filecount',section).textContent=[...groups.values()].reduce((n,a)=>n+a.length,0)+' / '+rows.length;
 for(const e of qa('[data-sort]',section))e.parentElement.setAttribute('aria-sort',e.dataset.sort===state.sort?(state.dir<0?'descending':'ascending'):'none');
 const groupOrder=[...groups].sort((a,b)=>state.sort==='count'?state.dir*(a[1].length-b[1].length)||a[0].localeCompare(b[0]):state.dir*a[0].localeCompare(b[0]));
 let out='';
 for(const [name,items] of groupOrder){
  const open=state.expandAll||state.forceOpen||state.opens.has(name);
  out+='<tr class="group-row"><td>'+items.length+'</td><td colspan="'+cols.length+'"><button data-group="'+esc(name)+'" aria-expanded="'+open+'">'+(open?'▾ ':'▸ ')+esc(name)+'</button></td></tr>';
  if(!open)continue;
  items.sort((a,b)=>state.sort==='count'?field(a,'title').localeCompare(field(b,'title')):state.dir*field(a,state.sort).localeCompare(field(b,state.sort)));
  for(const r of items){
   const relatedTests=data.research.tests.filter(t=>t.scene_ids?.includes(r.id));
   const body=[esc(field(r,'description')),esc(field(r,'site')),esc(field(r,'date_kind')),esc(field(r,'rights')),link(tr('Reuse terms','Условия использования'),r.rights_url),link(tr('Open source','Открыть источник'),r.url),...(r.assets||[]).map(a=>link(a.product,a.url)),...relatedTests.map(t=>innerLink(field(t,'title'),'tests',t.id)),innerLink(tr('Link to this record','Ссылка на запись'),kind,r.id)].filter(Boolean);
   out+='<tr data-rid="'+esc(r.id)+'"><td></td>'+cols.map(([k])=>k==='title'?'<td class="resource"><details class="entry"><summary>'+esc(field(r,'title'))+'</summary><p>'+body.join(' · ')+'</p></details></td>':'<td>'+esc(field(r,k)||'·')+'</td>').join('')+'</tr>';
  }
 }
 q('tbody',section).innerHTML=out||'<tr><td colspan="'+(cols.length+1)+'">'+tr('No matching records','Совпадений нет')+'</td></tr>';
 for(const e of qa('[data-group]',section))e.onclick=()=>{const name=e.dataset.group;if(state.forceOpen||state.expandAll){state.opens=new Set([...groups.keys()].filter(x=>x!==name));state.expandAll=false;state.forceOpen=false;state.closedSearch=true}else if(state.opens.has(name))state.opens.delete(name);else state.opens.add(name);fillTable(kind)};
}
function selectPage(scroll=false){
 const raw=location.hash.slice(1),cut=raw.indexOf('/'),page=cut<0?raw:raw.slice(0,cut);
 let id='';try{id=cut<0?'':decodeURIComponent(raw.slice(cut+1))}catch{}
 if(raw==='archiveLabel'){location.replace(pagesBase+'brief.html'+location.search+'#archiveLabel');return}
 if(/^[PL]\d+(?:\.\d+)?$/.test(raw)){location.replace(pagesBase+'decision-map.html'+location.search+'#'+raw);return}
 const name=Object.hasOwn(pageNames,page)?page:'overview';
 for(const s of qa('.panel'))s.classList.toggle('active',s.id===name);
 for(const a of qa('[data-page]')){if(a.dataset.page===name)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current')}
 if(!id)return;
 if(name==='method'&&id.startsWith('variant-')){
  const variant=data.research.candidate_family.variants.find(v=>v.id===id.slice(8));
  if(variant){const box=q('#method .node:last-child');box.open=true;for(const select of qa('select',box))select.value=String(variant[select.dataset.key]);q('select',box).dispatchEvent(new Event('change'));if(scroll)box.scrollIntoView({block:'nearest'})}
  return;
 }
 if(name==='tests'&&id.includes('/'))id=id.split('/')[0];
 if(tables[name]){
  const r=recordList(name).find(r=>r.id===id);if(!r)return;
  tables[name]=fresh();tables[name].opens.add(field(r,'group'));tableShell(name);
 }
 const item=qa('[data-rid]',q('#'+name)).find(e=>e.dataset.rid===id);
 if(item){const d=item.matches('details')?item:q('details',item);if(d)d.open=true;item.classList.add('target');if(scroll)requestAnimationFrame(()=>item.scrollIntoView({block:'nearest'}))}
}
function render(){
 document.documentElement.lang=lang;
 for(const [el,en] of original)el.textContent=lang==='ru'?overrides[el.dataset.copy]:en;
 for(const a of qa('[data-lang]')){const u=new URL(location.href);u.searchParams.set('lang',a.dataset.lang);a.href=u.href;a.setAttribute('aria-current',String(a.dataset.lang===lang))}
 for(const a of qa('[data-page]'))a.textContent=pageNames[a.dataset.page][lang==='ru'?1:0];
 q('#stamp').textContent=tr('Public research index','Публичный индекс исследования')+' · '+(data.as_of||'2026-11-27');
 overview();renderMethod();candidateGrid();renderTests();
 for(const kind of ['datasets','library']){tables[kind]=fresh();tableShell(kind)}
 selectPage(false);
}
render();
window.addEventListener('hashchange',()=>{selectPage(true);for(const a of qa('[data-lang]')){const u=new URL(location.href);u.searchParams.set('lang',a.dataset.lang);a.href=u.href}});
async function sync(){
 // These independent public releases can advance without a new site deployment.
 const names=['library','datasets','research'];
 const results=await Promise.allSettled(names.map(async n=>{const r=await fetch(pagesBase+'data/'+n+'.json',{cache:'no-cache'});if(!r.ok)throw Error(r.status);return r.json()}));
 let changed=false;
 for(let i=0;i<names.length;i++){
  const part=results[i];if(part.status!=='fulfilled')continue;
  const n=names[i],d=part.value;
  if(n==='research'?!(Array.isArray(d.stages)&&d.stages.length&&Array.isArray(d.tests)&&d.tests.length):!(Array.isArray(d.items)&&d.items.length))continue;
  if(JSON.stringify(data[n])!==JSON.stringify(d)){data[n]=d;changed=true}
 }
 try{
  const response=await fetch('https://api.github.com/repos/kravtsovd/giza-radar-check/git/trees/main?recursive=1');
  if(response.ok){const t=await response.json();if(!t.truncated&&t.tree?.some(f=>f.path==='data/ontology.json')){const files=t.tree.filter(f=>f.type==='blob'&&!f.path.startsWith('.')).map(f=>({path:f.path})).sort((a,b)=>a.path<b.path?-1:a.path>b.path?1:0);if(JSON.stringify(files)!==JSON.stringify(data.files)){data.files=files;changed=true}}}
 }catch{/* The embedded catalog also works offline. */}
 if(changed&&!document.querySelector('.controls :focus, details[open]'))render();
}
sync().catch(()=>{});
