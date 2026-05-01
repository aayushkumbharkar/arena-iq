/* ElectIQ — Frontend Application Logic v1.1 */

// ─── State ─────────────────────────────────────────────────
let chatHistory = [];
let quizData = [];
let quizIndex = 0;
let quizScore = 0;
let quizAnswered = false;
let currentLang = 'en';
let electionData = null;

// ─── Screen Reader Announce ────────────────────────────────
function srAnnounce(text) {
  const el = document.getElementById('sr-announce');
  if (el) { el.textContent = ''; setTimeout(() => { el.textContent = text; }, 50); }
}

// ─── Data Loading ──────────────────────────────────────────
async function loadElectionData() {
  try {
    const res = await fetch('/api/election-data');
    electionData = await res.json();
    renderAll();
  } catch (e) {
    console.error('Failed to load election data:', e);
  }
}

function renderAll() {
  renderTimeline();
  renderFacts();
  renderVoterInfo();
  renderVotingMethods();
  renderElectionTypes();
  renderStats();
}

// ─── Render Functions ──────────────────────────────────────
function renderTimeline() {
  const el = document.getElementById('timeline');
  if (!el || !electionData) return;
  el.innerHTML = electionData.process_steps.map(s =>
    `<div class="tl-item" tabindex="0" role="listitem button" aria-label="Step ${s.step}: ${s.title}"
      onclick="sendQuick('Tell me about step ${s.step}: ${s.title}')"
      onkeydown="if(event.key==='Enter'||event.key===' ')sendQuick('Tell me about step ${s.step}: ${s.title}')">
      <div class="tl-dot" aria-hidden="true"></div>
      <div class="tl-icon" aria-hidden="true">${s.icon}</div>
      <div class="tl-title">Step ${s.step}: ${s.title}</div>
      <div class="tl-desc">${s.description}</div>
    </div>`
  ).join('');
}

function renderFacts() {
  const el = document.getElementById('fact-text');
  if (!el || !electionData) return;
  const facts = electionData.quick_facts;
  let i = 0;
  el.textContent = facts[0];
  setInterval(() => { i = (i + 1) % facts.length; el.textContent = facts[i]; }, 8000);
}

function renderVoterInfo() {
  const el = document.getElementById('voter-info');
  if (!el || !electionData) return;
  const info = electionData.voter_info;
  el.innerHTML =
    '<div class="info-card" role="listitem"><div class="info-card-title">📋 Eligibility</div><ul class="info-list" aria-label="Voter eligibility criteria">' +
    info.eligibility.map(e => `<li>${e}</li>`).join('') +
    '</ul></div>' +
    '<div class="info-card" role="listitem"><div class="info-card-title">📝 Registration Steps</div><ul class="info-list" aria-label="Registration steps">' +
    info.registration_steps.map(s => `<li>${s}</li>`).join('') +
    '</ul></div>';
}

function renderVotingMethods() {
  const el = document.getElementById('voting-methods');
  if (!el || !electionData) return;
  el.innerHTML = electionData.voting_methods.map(m =>
    `<div class="info-card" role="listitem" tabindex="0"
      onclick="sendQuick('Explain ${m.name} voting method')"
      onkeydown="if(event.key==='Enter'||event.key===' ')sendQuick('Explain ${m.name} voting method')"
      aria-label="${m.name}: ${m.description}">
      <div class="info-card-title">${m.icon} ${m.name}</div>
      <div class="info-card-body">${m.description}</div>
    </div>`
  ).join('');
}

function renderElectionTypes() {
  const el = document.getElementById('election-types');
  if (!el || !electionData) return;
  el.innerHTML = electionData.election_types.map(t =>
    `<div class="info-card" role="listitem" tabindex="0"
      onclick="sendQuick('Tell me about ${t.name} elections')"
      onkeydown="if(event.key==='Enter'||event.key===' ')sendQuick('Tell me about ${t.name} elections')"
      aria-label="${t.name} elections, ${t.frequency}">
      <div class="info-card-title">${t.icon} ${t.name}</div>
      <div class="info-card-body">${t.description} · <strong>${t.frequency}</strong></div>
    </div>`
  ).join('');
}

function renderStats() {
  if (!electionData) return;
  document.getElementById('stat-steps').textContent = electionData.process_steps.length;
  document.getElementById('stat-methods').textContent = electionData.voting_methods.length;
  document.getElementById('stat-types').textContent = electionData.election_types.length;
  document.getElementById('stat-rights').textContent = electionData.voter_info.rights.length;
}

// ─── Language / Translation ────────────────────────────────
async function changeLanguage(lang) {
  if (lang === currentLang) return;
  currentLang = lang;

  if (lang === 'en') {
    renderAll();
    srAnnounce('Language switched to English');
    return;
  }

  const panels = ['voter-info', 'voting-methods', 'election-types', 'timeline'];
  panels.forEach(id => {
    const el = document.getElementById(id);
    if (el) el.classList.add('translating');
  });

  try {
    // Collect texts to translate
    const textsToTranslate = [];
    if (electionData) {
      electionData.process_steps.forEach(s => textsToTranslate.push(s.title, s.description));
      electionData.voting_methods.forEach(m => textsToTranslate.push(m.name, m.description));
      electionData.election_types.forEach(t => textsToTranslate.push(t.name, t.description));
    }

    const res = await fetch('/api/translate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ texts: textsToTranslate, target: lang }),
    });

    if (!res.ok) throw new Error('Translation API error');
    const data = await res.json();

    // Apply translations to a cloned data object
    const translated = JSON.parse(JSON.stringify(electionData));
    let idx = 0;
    translated.process_steps.forEach(s => { s.title = data.translations[idx++]; s.description = data.translations[idx++]; });
    translated.voting_methods.forEach(m => { m.name = data.translations[idx++]; m.description = data.translations[idx++]; });
    translated.election_types.forEach(t => { t.name = data.translations[idx++]; t.description = data.translations[idx++]; });

    // Temporarily use translated data
    const original = electionData;
    electionData = translated;
    renderTimeline(); renderVotingMethods(); renderElectionTypes(); renderVoterInfo();
    electionData = original;

    const langNames = { hi: 'Hindi', es: 'Spanish', fr: 'French' };
    srAnnounce(`Content translated to ${langNames[lang] || lang}`);
  } catch (e) {
    console.error('Translation failed:', e);
    srAnnounce('Translation unavailable, showing English content');
    renderAll();
  } finally {
    panels.forEach(id => {
      const el = document.getElementById(id);
      if (el) el.classList.remove('translating');
    });
  }
}

// ─── Chat ──────────────────────────────────────────────────
function renderMarkdown(text) {
  return text
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br>');
}

function addMessage(role, content) {
  const container = document.getElementById('messages');
  const div = document.createElement('div');
  div.className = `message ${role}`;
  div.setAttribute('role', 'article');
  const avatar = document.createElement('div');
  avatar.className = `avatar ${role}`;
  avatar.textContent = role === 'ai' ? '🗳️' : '👤';
  avatar.setAttribute('aria-hidden', 'true');
  const bubble = document.createElement('div');
  bubble.className = 'message-bubble';
  bubble.innerHTML = renderMarkdown(content);
  div.appendChild(avatar);
  div.appendChild(bubble);
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
  return div;
}

function showTyping() {
  const container = document.getElementById('messages');
  const div = document.createElement('div');
  div.className = 'message ai'; div.id = 'typing-indicator';
  div.setAttribute('role', 'status'); div.setAttribute('aria-label', 'ElectIQ is thinking');
  const avatar = document.createElement('div');
  avatar.className = 'avatar ai'; avatar.textContent = '🗳️';
  avatar.setAttribute('aria-hidden', 'true');
  const bubble = document.createElement('div');
  bubble.className = 'typing-indicator';
  bubble.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';
  div.appendChild(avatar); div.appendChild(bubble);
  container.appendChild(div); container.scrollTop = container.scrollHeight;
}

function removeTyping() {
  const t = document.getElementById('typing-indicator');
  if (t) t.remove();
}

async function sendMessage() {
  const input = document.getElementById('chat-input');
  const msg = input.value.trim();
  if (!msg) return;
  input.value = ''; input.style.height = 'auto';
  document.getElementById('send-btn').disabled = true;
  addMessage('user', msg);
  chatHistory.push({ role: 'user', content: msg });
  showTyping();
  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: msg, history: chatHistory.slice(-10) }),
    });
    const data = await res.json();
    removeTyping();
    const reply = data.response || "Sorry, I couldn't get a response.";
    addMessage('ai', reply);
    chatHistory.push({ role: 'model', content: reply });
    // Update page title with topic
    document.title = `ElectIQ — ${msg.slice(0, 40)}`;
  } catch (err) {
    removeTyping();
    addMessage('ai', '⚠️ Connection issue. Please try again.');
  }
  document.getElementById('send-btn').disabled = false;
  input.focus();
}

function sendQuick(msg) {
  document.getElementById('chat-input').value = msg;
  sendMessage();
}

// ─── Quiz ──────────────────────────────────────────────────
async function startQuiz() {
  quizIndex = 0; quizScore = 0; quizAnswered = false;
  const overlay = document.getElementById('quiz-modal');
  overlay.classList.add('active');
  // Move focus into modal
  setTimeout(() => {
    const closeBtn = document.getElementById('modal-close-btn');
    if (closeBtn) closeBtn.focus();
  }, 100);
  try {
    const res = await fetch('/api/quiz?count=5');
    const data = await res.json();
    quizData = data.questions || [];
  } catch (e) { quizData = []; }
  if (quizData.length === 0) {
    document.getElementById('quiz-content').innerHTML = '<p>Could not load quiz. Try again later.</p>';
    return;
  }
  renderQuizQuestion();
}

function renderQuizQuestion() {
  if (quizIndex >= quizData.length) { renderQuizScore(); return; }
  quizAnswered = false;
  const q = quizData[quizIndex];
  const el = document.getElementById('quiz-content');
  el.innerHTML =
    `<div style="font-size:0.7rem;color:var(--text-muted);margin-bottom:8px;" aria-label="Question ${quizIndex + 1} of ${quizData.length}">Question ${quizIndex + 1} of ${quizData.length}</div>
    <div class="quiz-question" id="quiz-q-text">${q.question}</div>
    <div id="quiz-options" role="group" aria-labelledby="quiz-q-text">${q.options.map((o, i) =>
      `<button class="quiz-option" onclick="answerQuiz(${i})" aria-label="Option ${i + 1}: ${o}">${o}</button>`
    ).join('')}</div>
    <div id="quiz-explain" aria-live="assertive"></div>
    <div class="quiz-nav"><div></div><button class="primary" id="quiz-next" onclick="nextQuiz()" style="display:none" aria-label="Next question">Next →</button></div>`;
  // Focus first option
  setTimeout(() => { const first = el.querySelector('.quiz-option'); if (first) first.focus(); }, 50);
}

function answerQuiz(idx) {
  if (quizAnswered) return;
  quizAnswered = true;
  const q = quizData[quizIndex];
  const btns = document.querySelectorAll('#quiz-options .quiz-option');
  btns.forEach((b, i) => {
    if (i === q.correct) b.classList.add('correct');
    else if (i === idx && idx !== q.correct) b.classList.add('wrong');
    b.disabled = true;
    b.setAttribute('aria-disabled', 'true');
  });
  const isCorrect = idx === q.correct;
  if (isCorrect) quizScore++;
  const resultText = isCorrect ? 'Correct!' : `Wrong. The correct answer is: ${q.options[q.correct]}`;
  if (q.explanation) {
    document.getElementById('quiz-explain').innerHTML =
      `<div class="quiz-explanation" role="status">💡 ${resultText} ${q.explanation}</div>`;
  }
  srAnnounce(resultText);
  document.getElementById('quiz-next').style.display = 'inline-block';
  document.getElementById('quiz-next').focus();
}

function nextQuiz() { quizIndex++; renderQuizQuestion(); }

function renderQuizScore() {
  const pct = Math.round((quizScore / quizData.length) * 100);
  const msg = pct >= 80 ? '🎉 Excellent!' : pct >= 50 ? '👍 Good effort!' : '📚 Keep learning!';
  document.getElementById('quiz-content').innerHTML =
    `<div class="quiz-score" role="status" aria-label="Quiz completed. Score: ${quizScore} out of ${quizData.length}, ${pct} percent">
      <div class="quiz-score-num">${quizScore}/${quizData.length}</div>
      <div style="font-size:0.9rem;margin-top:8px;">${msg}</div>
      <div style="font-size:0.78rem;color:var(--text-secondary);margin-top:4px;">You scored ${pct}%</div>
      <div class="quiz-nav" style="justify-content:center;margin-top:16px;">
        <button class="primary" onclick="startQuiz()">Try Again</button>
        <button onclick="closeQuiz()">Close</button>
      </div>
    </div>`;
  srAnnounce(`Quiz complete! You scored ${quizScore} out of ${quizData.length}, ${pct} percent. ${msg}`);
}

function closeQuiz() {
  document.getElementById('quiz-modal').classList.remove('active');
  document.title = 'ElectIQ — AI Election Process Education';
  // Return focus to quiz launcher
  const launcher = document.querySelector('.quiz-launcher');
  if (launcher) launcher.focus();
}

// ─── Focus Trap for Modal ──────────────────────────────────
document.getElementById('quiz-modal').addEventListener('keydown', function (e) {
  if (!this.classList.contains('active')) return;
  const focusable = this.querySelectorAll(
    'button:not([disabled]), [tabindex]:not([tabindex="-1"]), input, select, textarea'
  );
  const first = focusable[0];
  const last = focusable[focusable.length - 1];
  if (e.key === 'Tab') {
    if (e.shiftKey) {
      if (document.activeElement === first) { e.preventDefault(); last.focus(); }
    } else {
      if (document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
  }
  if (e.key === 'Escape') closeQuiz();
});

// ─── High Contrast Toggle ──────────────────────────────────
function toggleContrast() {
  document.body.classList.toggle('high-contrast');
  const btn = document.getElementById('hc-btn');
  const isHC = document.body.classList.contains('high-contrast');
  btn.textContent = isHC ? '◐ Normal' : '◑ High Contrast';
  srAnnounce(isHC ? 'High contrast mode enabled' : 'High contrast mode disabled');
}

// ─── Init ──────────────────────────────────────────────────
document.getElementById('chat-input').addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
});
document.getElementById('chat-input').addEventListener('input', function () {
  this.style.height = 'auto';
  this.style.height = Math.min(this.scrollHeight, 100) + 'px';
});
document.getElementById('quiz-modal').addEventListener('click', function (e) {
  if (e.target === this) closeQuiz();
});

loadElectionData();
