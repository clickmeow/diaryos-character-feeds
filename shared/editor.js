
const platforms = [["public_feed","Public Feed"],["private_moments","Moments"],["private_alt","Alt Account"]];
const fieldLabels = {phase:"Phase", timeline:"Date", event:"Event", post_id:"Post ID", content:"Post Text", image_file:"Image", unlock_condition:"Unlock", timestamp_mode:"Time Mode", notes:"Notes"};
let currentCharacter = "shatang";
let rows = [];
const $ = (id) => document.getElementById(id);
function status(text){ $("status").textContent = text; }
function esc(value){ return String(value ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c])); }
async function api(path, options){ const res = await fetch(path, options); if(!res.ok) throw new Error(await res.text()); return res.json(); }
async function loadCharacters(){
  const data = await api("/api/characters");
  const select = $("characterSelect");
  select.innerHTML = data.characters.map(c => `<option value="${esc(c.id)}">${esc(c.name)} (${esc(c.id)}, ${c.count})</option>`).join("");
  if(data.characters.some(c => c.id === currentCharacter)) select.value = currentCharacter;
  if(select.value) currentCharacter = select.value;
}
async function loadFeed(){ status("Loading..."); const data = await api(`/api/feed/${encodeURIComponent(currentCharacter)}`); rows = data.rows || []; render(); status(`Loaded ${rows.length} rows`); }
function updateRow(index, field, value){ rows[index][field] = value; }
function textarea(index, field, extra=""){ return `<textarea ${extra} data-index="${index}" data-field="${field}">${esc(rows[index][field] || "")}</textarea>`; }
function input(index, field, extra=""){ return `<input ${extra} data-index="${index}" data-field="${field}" value="${esc(rows[index][field] || "")}">`; }
function renderPost(row, index, platform){
  if((row.platform || "") !== platform) return "";
  const img = row.image_file ? `<img class="thumb" src="characters/${encodeURIComponent(currentCharacter)}/${esc(row.image_file)}" alt="">` : `<span class="muted">Drop or paste an image</span>`;
  return `<div class="post-card" data-index="${index}"><div class="post-head"><div class="post-id">${esc(fieldLabels.post_id)}</div>${input(index,"post_id")}</div><label>${esc(fieldLabels.content)}${textarea(index,"content")}</label><label>${esc(fieldLabels.image_file)}${input(index,"image_file")}</label>${img}<div class="dropzone" data-drop-index="${index}">Drop image here, or click then Ctrl+V paste image</div><label>${esc(fieldLabels.unlock_condition)}${input(index,"unlock_condition")}</label><label>${esc(fieldLabels.timestamp_mode)}${input(index,"timestamp_mode")}</label><label>${esc(fieldLabels.notes)}${textarea(index,"notes")}</label></div>`;
}
function groupRows(){ const map = new Map(); rows.forEach((row, index) => { const key = [row.phase || "", row.timeline || "", row.event || ""].join("|"); if(!map.has(key)) map.set(key, []); map.get(key).push({row, index}); }); return [...map.values()]; }
function render(){
  if(!rows.length){ $("app").innerHTML = `<div class="empty">No posts yet.</div>`; return; }
  let html = `<table class="flow-table editor-table"><thead><tr><th>Date</th><th>Event</th>${platforms.map(p=>`<th>${p[1]}</th>`).join("")}</tr></thead><tbody>`;
  for(const group of groupRows()){
    const first = group[0];
    html += `<tr><td><label>${esc(fieldLabels.phase)}${input(first.index,"phase")}</label><label>${esc(fieldLabels.timeline)}${input(first.index,"timeline")}</label></td><td class="event">${textarea(first.index,"event")}</td>`;
    for(const [platform] of platforms){ const cards = group.map(item => renderPost(item.row, item.index, platform)).filter(Boolean).join(""); html += `<td>${cards || `<span class="muted">None</span>`}</td>`; }
    html += `</tr>`;
  }
  html += `</tbody></table>`; $("app").innerHTML = html;
  document.querySelectorAll("textarea,input").forEach(el => el.addEventListener("input", e => updateRow(+e.target.dataset.index, e.target.dataset.field, e.target.value)));
  document.querySelectorAll(".dropzone").forEach(el => { el.addEventListener("dragover", e => { e.preventDefault(); el.classList.add("drag"); }); el.addEventListener("dragleave", () => el.classList.remove("drag")); el.addEventListener("drop", e => { e.preventDefault(); el.classList.remove("drag"); const file = e.dataTransfer.files[0]; if(file) uploadImage(+el.dataset.dropIndex, file); }); el.addEventListener("click", () => { document.querySelectorAll(".dropzone").forEach(z => z.classList.remove("drag")); el.classList.add("drag"); window.activeDropIndex = +el.dataset.dropIndex; }); });
}
async function uploadImage(index, file){ const reader = new FileReader(); reader.onload = async () => { status("Saving image..."); const postId = rows[index].post_id || `post_${index+1}`; const data = await api(`/api/upload/${encodeURIComponent(currentCharacter)}/${encodeURIComponent(postId)}`, {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({post_id:postId, data_url:reader.result})}); rows[index].image_file = data.image_file; render(); status(`Image saved: ${data.filename}`); }; reader.readAsDataURL(file); }
async function saveFeed(){ status("Saving..."); await api(`/api/feed/${encodeURIComponent(currentCharacter)}`, {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({rows})}); status(`Saved ${rows.length} rows`); }
document.addEventListener("paste", e => { const file = [...(e.clipboardData?.files || [])].find(f => f.type.startsWith("image/")); if(file && Number.isInteger(window.activeDropIndex)) uploadImage(window.activeDropIndex, file); });
$("characterSelect").addEventListener("change", async e => { currentCharacter = e.target.value; await loadFeed(); });
$("reloadBtn").addEventListener("click", loadFeed); $("saveBtn").addEventListener("click", saveFeed); $("renderHintBtn").addEventListener("click", () => status("After saving, run: python shared\\render_feed.py"));
(async function init(){ try{ await loadCharacters(); await loadFeed(); } catch(err){ status("Error: " + err.message); } })();
