/* ============================================================
   SANKALP — shared state layer (localStorage only, no backend)
   ============================================================ */

const STORE = {
  sadhana:  'sankalp.sadhana.v1',   // { 'YYYY-MM-DD': { key: true, ... } }
  streak:   'sankalp.streak.v1',    // { count: n, lastFullDate: 'YYYY-MM-DD' }
  thoughts: 'sankalp.thoughts.v1',  // [{id, text, ts}]
  gallery:  'sankalp.gallery.v1',   // [{id, url, videoId, note, ts}]
  journal:  'sankalp.journal.v1',   // { 'YYYY-MM-DD': { ...fields, synced, updatedAt } }
  github:   'sankalp.github.v1',    // { owner, repo, path, journalPath, token }
  lastSync: 'sankalp.lastSync.v1',  // epoch ms of last successful sync
};

const PRACTICES = [
  { key: 'kriya',   label: 'Shambhavi Kriya',  note: 'Inner Engineering' },
  { key: 'breath',  label: 'Breath Watching',  note: 'stillness practice' },
  { key: 'listen',  label: 'Sadhguru',         note: 'morning & evening' },
  { key: 'remember',label: 'Mother & Aunty',   note: 'remembrance' },
  { key: 'art',     label: 'Art',              note: 'creative practice' },
];

function todayKey(){
  const d = new Date();
  return d.getFullYear() + '-' + String(d.getMonth()+1).padStart(2,'0') + '-' + String(d.getDate()).padStart(2,'0');
}

function readJSON(key, fallback){
  try{
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  }catch(e){ return fallback; }
}
function writeJSON(key, value){
  localStorage.setItem(key, JSON.stringify(value));
}

/* ---------- sadhana ---------- */
function getSadhanaAll(){ return readJSON(STORE.sadhana, {}); }
function getSadhanaToday(){
  const all = getSadhanaAll();
  return all[todayKey()] || {};
}
function toggleSadhana(key){
  const all = getSadhanaAll();
  const tk = todayKey();
  if(!all[tk]) all[tk] = {};
  all[tk][key] = !all[tk][key];
  writeJSON(STORE.sadhana, all);
  updateStreak(all[tk]);
  return all[tk];
}
function updateStreak(todayState){
  const allDone = PRACTICES.every(p => todayState[p.key]);
  const s = readJSON(STORE.streak, { count: 0, lastFullDate: null });
  const tk = todayKey();
  if(allDone){
    if(s.lastFullDate === tk) { /* already counted today */ }
    else{
      const y = new Date(); y.setDate(y.getDate()-1);
      const yKey = y.getFullYear() + '-' + String(y.getMonth()+1).padStart(2,'0') + '-' + String(y.getDate()).padStart(2,'0');
      s.count = (s.lastFullDate === yKey) ? s.count + 1 : 1;
      s.lastFullDate = tk;
    }
  } else if(s.lastFullDate === tk){
    s.lastFullDate = null;
    s.count = Math.max(0, s.count - 1);
  }
  writeJSON(STORE.streak, s);
}
function getStreak(){ return readJSON(STORE.streak, { count: 0, lastFullDate: null }); }

/* ---------- thoughts ---------- */
function getThoughts(){ return readJSON(STORE.thoughts, []); }
function addThought(text){
  const list = getThoughts();
  list.unshift({ id: Date.now().toString(36), text, ts: new Date().toISOString() });
  writeJSON(STORE.thoughts, list);
  return list;
}
function deleteThought(id){
  const list = getThoughts().filter(t => t.id !== id);
  writeJSON(STORE.thoughts, list);
  return list;
}

/* ---------- gallery ---------- */
function extractYouTubeId(url){
  const m = url.match(/(?:youtu\.be\/|v=|\/embed\/|\/shorts\/)([A-Za-z0-9_-]{11})/);
  return m ? m[1] : null;
}
function getGallery(){ return readJSON(STORE.gallery, []); }
function addGalleryItem(url, note){
  const videoId = extractYouTubeId(url);
  const list = getGallery();
  list.unshift({ id: Date.now().toString(36), url, videoId, note, ts: new Date().toISOString() });
  writeJSON(STORE.gallery, list);
  return list;
}
function deleteGalleryItem(id){
  const list = getGallery().filter(g => g.id !== id);
  writeJSON(STORE.gallery, list);
  return list;
}

/* ---------- journal ---------- */
function getJournalAll(){ return readJSON(STORE.journal, {}); }
function getJournalEntry(date){ return getJournalAll()[date] || null; }

function saveJournalEntry(date, fields){
  const all = getJournalAll();
  const existing = all[date] || {};
  all[date] = { ...existing, ...fields, date, updatedAt: new Date().toISOString(), synced: false };
  writeJSON(STORE.journal, all);
  return all[date];
}

function markJournalSynced(dates){
  const all = getJournalAll();
  dates.forEach(d => { if(all[d]) all[d].synced = true; });
  writeJSON(STORE.journal, all);
}

function getUnsyncedJournal(){
  return Object.values(getJournalAll()).filter(e => !e.synced && e.date);
}

function journalDayName(dateStr){
  const d = new Date(dateStr + 'T12:00:00');
  return d.toLocaleDateString('en-IN', { weekday: 'long' });
}

function entryToMarkdown(e){
  const day = journalDayName(e.date);
  const rating = e.self_rating != null ? e.self_rating : '';
  return [
    `---`,
    `date: ${e.date}`,
    `day: ${day}`,
    `self_rating: ${rating}`,
    `---`,
    ``,
    `# ${e.date} — ${day}`,
    ``,
    `## Morning Plan`,
    ``,
    `**Sadhana**`,
    e.sadhana_plan || '',
    ``,
    `**Learning**`,
    e.learning_plan || '',
    ``,
    `**Work**`,
    e.work_plan || '',
    ``,
    `**Sankalp** (intention for the day)`,
    e.sankalp ? `> ${e.sankalp}` : `>`,
    ``,
    `---`,
    ``,
    `## Evening Reflection`,
    ``,
    `**Sadhana** — did it happen? How did it feel?`,
    e.sadhana_ref || '',
    ``,
    `**Learning** — what actually got learned?`,
    e.learning_ref || '',
    ``,
    `**Work** — what shipped / moved / got stuck?`,
    e.work_ref || '',
    ``,
    `**Gratitude** — one thing:`,
    e.gratitude || '',
    ``,
    `**Friction** — what pulled me off-plan today?`,
    e.friction || '',
    ``,
    `**Tomorrow's first move:**`,
    e.tomorrow || '',
    ``,
  ].join('\n');
}

/* ============================================================
   GITHUB SYNC — data lives in localStorage all day.
   One click pushes the full snapshot + any new journal entries
   as individual markdown files to your GitHub repo.
   ============================================================ */

function getGithubConfig(){ return readJSON(STORE.github, null); }
function saveGithubConfig(cfg){ writeJSON(STORE.github, cfg); }
function clearGithubConfig(){ localStorage.removeItem(STORE.github); }
function getLastSync(){ return Number(localStorage.getItem(STORE.lastSync) || 0); }

function utf8ToBase64(str){ return btoa(unescape(encodeURIComponent(str))); }

function encodeGithubPath(path){
  return path.split('/').map(encodeURIComponent).join('/');
}

async function githubGetFile(cfg, filePath){
  const path = filePath || cfg.path;
  const res = await fetch(
    `https://api.github.com/repos/${cfg.owner}/${cfg.repo}/contents/${encodeGithubPath(path)}`,
    { headers: { Authorization: `token ${cfg.token}`, Accept: 'application/vnd.github+json' } }
  );
  if(res.status === 404) return null;
  if(!res.ok){
    const body = await res.json().catch(()=>({}));
    throw new Error(body.message || `GitHub error (${res.status}) reading file`);
  }
  return res.json();
}

async function githubPutFile(cfg, filePath, contentStr, message, sha){
  const path = filePath || cfg.path;
  const body = {
    message,
    content: utf8ToBase64(contentStr),
    committer: { name: cfg.owner, email: `${cfg.owner}@users.noreply.github.com` },
  };
  if(sha) body.sha = sha;

  const res = await fetch(
    `https://api.github.com/repos/${cfg.owner}/${cfg.repo}/contents/${encodeGithubPath(path)}`,
    {
      method: 'PUT',
      headers: {
        Authorization: `token ${cfg.token}`,
        Accept: 'application/vnd.github+json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    }
  );
  if(!res.ok){
    const err = await res.json().catch(()=>({}));
    throw new Error(err.message || `GitHub error (${res.status}) writing file`);
  }
  return res.json();
}

/**
 * Pushes:
 * 1. sankalp-data.json — full snapshot of all data (including journal JSON)
 * 2. journal/entries/YYYY/MM/YYYY-MM-DD.md — one file per unsynced journal entry
 */
async function syncToGithub(){
  const cfg = getGithubConfig();
  if(!cfg || !cfg.token || !cfg.owner || !cfg.repo){
    throw new Error('NO_CONFIG');
  }

  const lastSync = getLastSync();
  const thoughts = getThoughts();
  const gallery = getGallery();
  const newThoughts = thoughts.filter(t => new Date(t.ts).getTime() > lastSync);
  const newGallery = gallery.filter(g => new Date(g.ts).getTime() > lastSync);
  const todayState = getSadhanaToday();
  const doneToday = PRACTICES.filter(p => todayState[p.key]).length;
  const unsyncedJournal = getUnsyncedJournal();

  if(newThoughts.length === 0 && newGallery.length === 0 && doneToday === 0 && unsyncedJournal.length === 0){
    throw new Error('NOTHING_NEW');
  }

  // Build commit message
  const parts = [];
  if(newThoughts.length) parts.push(`${newThoughts.length} thought${newThoughts.length > 1 ? 's' : ''}`);
  if(newGallery.length) parts.push(`${newGallery.length} video${newGallery.length > 1 ? 's' : ''}`);
  if(unsyncedJournal.length) parts.push(`${unsyncedJournal.length} journal entr${unsyncedJournal.length > 1 ? 'ies' : 'y'}`);
  parts.push(`${doneToday}/5 sadhana`);
  const dateStr = new Date().toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
  const message = `Sankalp sync — ${parts.join(', ')} — ${dateStr}`;

  // 1. Push full JSON snapshot (includes journal data)
  const snapshot = {
    exportedAt: new Date().toISOString(),
    sadhana: getSadhanaAll(),
    streak: getStreak(),
    thoughts,
    gallery,
    journal: getJournalAll(),
  };
  const mainPath = cfg.path || 'sankalp-data.json';
  const existingMain = await githubGetFile(cfg, mainPath);
  await githubPutFile(cfg, mainPath, JSON.stringify(snapshot, null, 2), message, existingMain ? existingMain.sha : undefined);

  // 2. Push each unsynced journal entry as a markdown file
  const journalBase = cfg.journalPath || 'journal/entries';
  const syncedDates = [];
  for(const entry of unsyncedJournal){
    const [year, month] = entry.date.split('-');
    const filePath = `${journalBase}/${year}/${month}/${entry.date}.md`;
    try{
      const existingMd = await githubGetFile(cfg, filePath);
      await githubPutFile(cfg, filePath, entryToMarkdown(entry), `journal: ${entry.date}`, existingMd ? existingMd.sha : undefined);
      syncedDates.push(entry.date);
    }catch(e){
      console.warn('Could not sync journal entry', entry.date, e.message);
    }
  }
  if(syncedDates.length > 0) markJournalSynced(syncedDates);

  localStorage.setItem(STORE.lastSync, Date.now().toString());
  return { message, newThoughts: newThoughts.length, newGallery: newGallery.length, doneToday, syncedJournal: syncedDates.length };
}

/* ---------- formatting ---------- */
function formatDate(iso){
  const d = new Date(iso);
  return d.toLocaleDateString('en-IN', { day:'numeric', month:'short', year:'numeric' }) +
         ' · ' + d.toLocaleTimeString('en-IN', { hour:'2-digit', minute:'2-digit' });
}
function timeOfDayGreeting(){
  const h = new Date().getHours();
  if(h < 5) return 'Still night';
  if(h < 12) return 'Good morning';
  if(h < 17) return 'Good afternoon';
  if(h < 20) return 'Good evening';
  return 'Good night';
}
