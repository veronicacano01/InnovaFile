document.addEventListener('DOMContentLoaded', () => {
  const sidebar = document.querySelector('.innova-sidebar');
  const toggle = document.querySelector('[data-sidebar-toggle]');
  if (toggle && sidebar) toggle.addEventListener('click', () => sidebar.classList.toggle('open'));
  document.addEventListener('click', (e) => {
    if (window.innerWidth < 992 && sidebar?.classList.contains('open') && !sidebar.contains(e.target) && !toggle?.contains(e.target)) sidebar.classList.remove('open');
  });
  document.querySelectorAll('[data-password-toggle]').forEach(btn => btn.addEventListener('click', () => {
    const input = document.querySelector(btn.dataset.passwordToggle);
    if (!input) return;
    input.type = input.type === 'password' ? 'text' : 'password';
    btn.innerHTML = input.type === 'password' ? '<i class="bi bi-eye"></i>' : '<i class="bi bi-eye-slash"></i>';
  }));
});

(function(){
 const connect=document.getElementById('connect-folder'), fallback=document.getElementById('folder-fallback'), status=document.getElementById('sync-status'), wrap=document.getElementById('sync-progress-wrap'), bar=document.getElementById('sync-progress');
 if(!connect)return;
 const DB='innovafile-local';
 function db(){return new Promise((res,rej)=>{const r=indexedDB.open(DB,1);r.onupgradeneeded=()=>r.result.createObjectStore('handles');r.onsuccess=()=>res(r.result);r.onerror=()=>rej(r.error)})}
 async function save(h){const d=await db();return new Promise((res,rej)=>{const t=d.transaction('handles','readwrite');t.objectStore('handles').put(h,'documents');t.oncomplete=res;t.onerror=()=>rej(t.error)})}
 async function get(){const d=await db();return new Promise((res,rej)=>{const t=d.transaction('handles','readonly'),r=t.objectStore('handles').get('documents');r.onsuccess=()=>res(r.result);r.onerror=()=>rej(r.error)})}
 async function allowed(h){try{return await h.queryPermission({mode:'read'})==='granted'}catch(e){return false}}
 async function send(file,path,index,total){const fd=new FormData();fd.append('file',file,file.name);fd.append('source_path',path);const r=await fetch('/documents/auto-import',{method:'POST',body:fd,credentials:'same-origin'});const d=await r.json();if(!d.ok)throw new Error(d.message||file.name);bar.style.width=Math.round(((index+1)/total)*100)+'%';return d}
 async function scan(h){const all=[];async function walk(dir,prefix=''){for await(const [name,e] of dir.entries()){if(e.kind==='file')all.push([e,prefix+name]);else if(e.kind==='directory'&&!name.startsWith('.'))await walk(e,prefix+name+'/')}}await walk(h);const ex=['pdf','doc','docx','xls','xlsx','ppt','pptx','txt','csv','jpg','jpeg','png'];const files=all.filter(([e])=>ex.includes(e.name.split('.').pop().toLowerCase()));wrap.classList.remove('d-none');bar.style.width='0%';status.textContent=`Analizando ${files.length} documentos automáticamente...`;let ok=0,err=0;for(let i=0;i<files.length;i++){try{const f=await files[i][0].getFile();await send(f,files[i][1],i,files.length);ok++}catch(e){err++;console.warn(e)}}bar.style.width='100%';status.textContent=`Listo. ${ok} documento(s) sincronizado(s)${err?` y ${err} con error.`:'.'}`;if(ok)setTimeout(()=>location.reload(),1200)}
 async function connectFolder(){try{if(window.showDirectoryPicker){const h=await window.showDirectoryPicker({mode:'read'});await save(h);await scan(h)}else fallback.click()}catch(e){status.textContent='No se pudo conectar la carpeta. Inténtalo de nuevo.';console.warn(e)}}
 connect.addEventListener('click',connectFolder);
 fallback.addEventListener('change',async()=>{const files=Array.from(fallback.files||[]);if(!files.length)return;wrap.classList.remove('d-none');status.textContent=`Analizando ${files.length} documentos automáticamente...`;let ok=0;for(let i=0;i<files.length;i++){try{await send(files[i],files[i].webkitRelativePath||files[i].name,i,files.length);ok++}catch(e){console.warn(e)}}status.textContent=`Listo. ${ok} documento(s) sincronizado(s).`;if(ok)setTimeout(()=>location.reload(),1200)});
 (async()=>{try{const h=await get();if(h&&await allowed(h)){status.textContent='Carpeta conectada. Buscando documentos nuevos...';await scan(h)}}catch(e){}})();
})();
