const consentModal = document.getElementById('consent-modal');
const consentAccept = document.getElementById('consent-accept');

function hasConsented() {
  try { return localStorage.getItem('careai_consent_given') === 'true'; }
  catch (e) { return false; }
}
function recordConsent() {
  try { localStorage.setItem('careai_consent_given', 'true'); }
  catch (e) {}
}
if (hasConsented()) consentModal.classList.add('hidden');
consentAccept.addEventListener('click', () => {
  recordConsent();
  consentModal.classList.add('hidden');
});

const form = document.getElementById('chat-form');
const messageInput = document.getElementById('message-input');
const imageInput = document.getElementById('image-input');
const chatWindow = document.getElementById('chat-window');
const attachmentChip = document.getElementById('attachment-chip');
const attachmentName = document.getElementById('attachment-name');
const attachmentRemove = document.getElementById('attachment-remove');

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

function clearEmptyState() {
  const empty = chatWindow.querySelector('.empty-state');
  if (empty) empty.remove();
}

function addRow(html, who) {
  clearEmptyState();
  const row = document.createElement('div');
  row.className = `msg-row ${who}`;

  const avatar = document.createElement('div');
  avatar.className = `avatar ${who}`;
  avatar.innerHTML = who === 'user'
    ? '<svg viewBox="0 0 24 24"><circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 3.5-7 8-7s8 3 8 7"/></svg>'
    : '<svg viewBox="0 0 24 24"><path d="M3 12h4l2-7 4 14 2-7h6"/></svg>';

  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  bubble.innerHTML = html;

  row.appendChild(avatar);
  row.appendChild(bubble);
  chatWindow.appendChild(row);
  chatWindow.scrollTop = chatWindow.scrollHeight;
  return bubble;
}

function fieldRow(iconSvg, label, value, doctorClass) {
  return `<div class="result-field ${doctorClass || ''}">
    <div class="icon">${iconSvg}</div>
    <div class="field-body"><div class="k">${label}</div><div class="v">${escapeHtml(value)}</div></div>
  </div>`;
}

const ICONS = {
  pill: '<svg viewBox="0 0 24 24"><g transform="rotate(-45 12 12)"><rect x="2" y="9" width="20" height="6" rx="3"/><line x1="12" y1="9" x2="12" y2="15"/></g></svg>',
  leaf: '<svg viewBox="0 0 24 24"><path d="M5 21c8-1 13-6 14-14-8 1-13 6-14 14z"/><path d="M9 15c2-2 4-4 8-8"/></svg>',
  alert: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><line x1="12" y1="8" x2="12" y2="16"/><line x1="8" y1="12" x2="16" y2="12"/></svg>',
  link: '<svg viewBox="0 0 24 24"><path d="M9 15l6-6"/><path d="M11 6l1-1a3.5 3.5 0 015 5l-1 1"/><path d="M13 18l-1 1a3.5 3.5 0 01-5-5l1-1"/></svg>',
  warn: '<svg viewBox="0 0 24 24"><path d="M12 3l10 18H2L12 3z"/><line x1="12" y1="9" x2="12" y2="14"/></svg>',
};

function renderAssistantResponse(data) {
  if (data.emergency) {
    const html = `<div class="emergency-title">${ICONS.warn}${escapeHtml(data.message)}</div>
      <div class="field-body"><div class="k">Reason</div><div class="v">${escapeHtml(data.reason)}</div></div>`;
    const b = addRow(html, 'assistant');
    b.classList.add('emergency');
    return;
  }

  if (data.condition_matched) {
    let html = `<div class="result-card">
      <span class="result-title">${data.condition_matched}</span>`;
    if (data.visual_description) {
      html += `<div class="visual-note">What the photo shows: ${escapeHtml(data.visual_description)}</div>`;
    }
    html += fieldRow(ICONS.pill, 'Remedy', data.remedy);
    html += fieldRow(ICONS.leaf, 'Diet', data.diet);
    html += fieldRow(ICONS.alert, 'See a doctor if', data.see_a_doctor_if, 'doctor');
    html += `<div class="result-footer">${ICONS.link}<a href="${data.source_url}" target="_blank">${escapeHtml(data.source)}</a></div>
      <div class="result-footer">${escapeHtml(data.disclaimer)}</div></div>`;
    addRow(html, 'assistant');
    return;
  }

  let html = `<div>${escapeHtml(data.reply)}</div>`;
  if (data.visual_description) {
    html += `<div class="visual-note">What the photo shows: ${escapeHtml(data.visual_description)}</div>`;
  }
  html += `<div class="result-footer">${escapeHtml(data.disclaimer)}</div>`;
  addRow(html, 'assistant');
}

imageInput.addEventListener('change', () => {
  const file = imageInput.files[0];
  if (file) {
    attachmentName.textContent = file.name;
    attachmentChip.classList.remove('hidden');
  }
});
attachmentRemove.addEventListener('click', () => {
  imageInput.value = '';
  attachmentChip.classList.add('hidden');
});

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const message = messageInput.value.trim();
  const file = imageInput.files[0];
  if (!message && !file) return;

  addRow(escapeHtml(message || '(photo only)'), 'user');
  messageInput.value = '';
  imageInput.value = '';
  attachmentChip.classList.add('hidden');

  try {
    let response;
    if (file) {
      const formData = new FormData();
      if (message) formData.append('message', message);
      formData.append('image', file);
      response = await fetch('/chat-with-image', { method: 'POST', body: formData });
    } else {
      response = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message }),
      });
    }
    const data = await response.json();
    renderAssistantResponse(data);
  } catch (err) {
    addRow('Something went wrong reaching the server. Please try again.', 'assistant');
  }
});