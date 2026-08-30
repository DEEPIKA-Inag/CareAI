const form = document.getElementById('chat-form');
const messageInput = document.getElementById('message-input');
const imageInput = document.getElementById('image-input');
const chatWindow = document.getElementById('chat-window');

function addMessage(html, cls) {
  const div = document.createElement('div');
  div.className = `message ${cls}`;
  div.innerHTML = html;
  chatWindow.appendChild(div);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

function renderAssistantResponse(data) {
  if (data.emergency) {
    addMessage(`<strong>${escapeHtml(data.message)}</strong><div class="field-label">Reason</div>${escapeHtml(data.reason)}`, 'assistant emergency');
    return;
  }
  if (data.condition_matched) {
    let html = `<div class="field-label">Matched</div>${escapeHtml(data.condition_matched)}`;
    if (data.visual_description) html += `<div class="field-label">What the photo shows</div>${escapeHtml(data.visual_description)}`;
    html += `<div class="field-label">Remedy</div>${escapeHtml(data.remedy)}`;
    html += `<div class="field-label">Diet</div>${escapeHtml(data.diet)}`;
    html += `<div class="field-label">See a doctor if</div>${escapeHtml(data.see_a_doctor_if)}`;
    html += `<div class="disclaimer-line">Source: <a href="${data.source_url}" target="_blank">${escapeHtml(data.source)}</a><br>${escapeHtml(data.disclaimer)}</div>`;
    addMessage(html, 'assistant');
    return;
  }
  let html = escapeHtml(data.reply);
  if (data.visual_description) html += `<div class="field-label">What the photo shows</div>${escapeHtml(data.visual_description)}`;
  html += `<div class="disclaimer-line">${escapeHtml(data.disclaimer)}</div>`;
  addMessage(html, 'assistant');
}

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const message = messageInput.value.trim();
  const file = imageInput.files[0];
  if (!message && !file) return;

  addMessage(escapeHtml(message || '(photo only)'), 'user');
  messageInput.value = '';
  imageInput.value = '';

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
    addMessage('Something went wrong reaching the server. Please try again.', 'assistant emergency');
  }
});