// Beauty Pulse · Apps Script web app.
// The page and its data live in one Drive folder (dashboard.html + data/*.txt files, all at the top level of the folder).
// To update the dashboard, upload the new files into that folder; no code change or redeploy is needed.
// Deploy as a web app: Execute as "Me", Who has access "Anyone within Namshi".
const FOLDER_ID = 'PASTE_DRIVE_FOLDER_ID_HERE';
const PART = 2 * 1024 * 1024;   // data is returned to the page in 2 MB pieces

function doGet() {
  return HtmlService.createHtmlOutput(readFile_('dashboard.html'))
    .setTitle('Beauty Pulse')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1');
}

// newest file with this name in the folder (so uploading a new copy is enough, even if Drive keeps the old one)
function file_(name) {
  const it = DriveApp.getFolderById(FOLDER_ID).getFilesByName(name);
  let best = null;
  while (it.hasNext()) { const f = it.next(); if (!best || f.getLastUpdated() > best.getLastUpdated()) best = f; }
  if (!best) throw new Error('Missing file in the Drive folder: ' + name);
  return best;
}
function readFile_(name) { return file_(name).getBlob().getDataAsString(); }

// page -> data file piece i of name.txt; returns { n: number of pieces, s: text }
function getData(name, i) {
  if (!/^[A-Za-z0-9_]+$/.test(name)) throw new Error('bad name');
  const t = readFile_(name + '.txt');
  return { n: Math.max(1, Math.ceil(t.length / PART)), s: t.slice(i * PART, (i + 1) * PART) };
}

// ---- Brand POC access: the owner plus the emails the owner adds (stored in Script Properties) ----
function me_() { return (Session.getActiveUser().getEmail() || '').toLowerCase(); }
function isOwner_() { const m = me_(); return !!m && m === (Session.getEffectiveUser().getEmail() || '').toLowerCase(); }
function pocIds_() { return JSON.parse(PropertiesService.getScriptProperties().getProperty('POC_IDS') || '[]'); }

function whoAmI() {
  const id = me_(), owner = isOwner_();
  return { id: id, isOwner: owner, poc: owner || (!!id && pocIds_().indexOf(id) >= 0) };
}
// the owner sees the full list; anyone else only learns whether they are on it
function getPocIds() { return isOwner_() ? pocIds_() : (whoAmI().poc ? [me_()] : []); }
function setPocIds(ids) {
  if (!isOwner_()) throw new Error('Only the owner can change Brand POC access');
  const clean = (ids || []).map(x => String(x).trim().toLowerCase()).filter(x => /^[^@\s]+@[^@\s]+$/.test(x));
  PropertiesService.getScriptProperties().setProperty('POC_IDS', JSON.stringify([...new Set(clean)]));
  return pocIds_();
}
