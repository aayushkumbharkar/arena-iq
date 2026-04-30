/* ElectIQ — Frontend Application Logic */

// ─── State ─────────────────────────────────────────────────
let chatHistory = [];
let quizData = [];
let quizIndex = 0;
let quizScore = 0;
let quizAnswered = false;

// ─── Data Loading ──────────────────────────────────────────
let electionData = null;

async function loadElectionData() {
  try {
    const res = await fetch('/api/election-data');
    electionData = await res.json();
    renderTimeline();
    renderFacts();
    renderVoterInfo();
    renderVotingMethods();
    renderElectionTypes();
    renderStats();
  } catch (e) {
    console.error('Failed to load election data:', e);
  }
}

// ─── Render Functions ──────────────────────────────────────
function renderTimeline() {
  const el = document.getElementById('timeline');
  if (!el || !electionData) return;
  el.innerHTML = electionData.process_steps.map(s =>
    `<div class="tl-item" tabindex="0" role="button" aria-label="Step ${s.step}: ${s.title}" onclick="sendQuick('Tell me about step ${s.step}: ${s.title}')">
      <div class="tl-dot"></div>
      <div class="tl-icon">${s.icon}</div>
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
    '<div class="info-card"><div class="info-card-title">📋 Eligibility</div><ul class="info-list">' +
    info.eligibility.map(e => `<li>${e}</li>`).join('') +
    '</ul></div>' +
    '<div class="info-card"><div class="info-card-title">📝 Registration Steps</div><ul class="info-list">' +
    info.registration_steps.map(s => `<li>${s}</li>`).join('') +
    '</ul></div>';
}

function renderVotingMethods() {
  const el = document.getElementById('voting-methods');
  if (!el || !electionData) return;
  el.innerHTML = electionData.voting_methods.map(m =>
    `<div class="info-card" tabindex="0" onclick="sendQuick('Explain ${m.name} voting method')">
      <div class="info-card-title">${m.icon} ${m.name}</div>
      <div class="info-card-body">${m.description}</div>
    </div>`
  ).join('');
}

function renderElectionTypes() {
  const el = document.getElementById('election-types');
  if (!el || !electionData) return;
  el.innerHTML = electionData.election_types.map(t =>
    `<div class="info-card" tabindex="0" onclick="sendQuick('Tell me about ${t.name} elections')">
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
      body: JSON.stringify({ message: msg, history: chatHistory.slice(-10) })
    });
    const data = await res.json();
    removeTyping();
    const reply = data.response || "Sorry, I couldn't get a response.";
    addMessage('ai', reply);
    chatHistory.push({ role: 'model', content: reply });
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
    `<div style="font-size:0.7rem;color:var(--text-muted);margin-bottom:8px;">Question ${quizIndex+1} of ${quizData.length}</div>
    <div class="quiz-question">${q.question}</div>
    <div id="quiz-options">${q.options.map((o,i) =>
      `<button class="quiz-option" onclick="answerQuiz(${i})" aria-label="Option: ${o}">${o}</button>`
    ).join('')}</div>
    <div id="quiz-explain"></div>
    <div class="quiz-nav"><div></div><button class="primary" id="quiz-next" onclick="nextQuiz()" style="display:none">Next →</button></div>`;
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
  });
  if (idx === q.correct) quizScore++;
  if (q.explanation) {
    document.getElementById('quiz-explain').innerHTML = `<div class="quiz-explanation">💡 ${q.explanation}</div>`;
  }
  document.getElementById('quiz-next').style.display = 'inline-block';
}

function nextQuiz() { quizIndex++; renderQuizQuestion(); }

function renderQuizScore() {
  const pct = Math.round((quizScore / quizData.length) * 100);
  document.getElementById('quiz-content').innerHTML =
    `<div class="quiz-score">
      <div class="quiz-score-num">${quizScore}/${quizData.length}</div>
      <div style="font-size:0.9rem;margin-top:8px;">${pct >= 80 ? '🎉 Excellent!' : pct >= 50 ? '👍 Good effort!' : '📚 Keep learning!'}</div>
      <div style="font-size:0.78rem;color:var(--text-secondary);margin-top:4px;">You scored ${pct}%</div>
      <div class="quiz-nav" style="justify-content:center;margin-top:16px;">
        <button class="primary" onclick="startQuiz()">Try Again</button>
        <button onclick="closeQuiz()">Close</button>
      </div>
    </div>`;
}

function closeQuiz() { document.getElementById('quiz-modal').classList.remove('active'); }

// ─── High Contrast Toggle ──────────────────────────────────
function toggleContrast() {
  document.body.classList.toggle('high-contrast');
  const btn = document.getElementById('hc-btn');
  btn.textContent = document.body.classList.contains('high-contrast') ? '◐ Normal' : '◑ High Contrast';
}

// ─── Init ──────────────────────────────────────────────────
document.getElementById('chat-input').addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
});
document.getElementById('chat-input').addEventListener('input', function() {
  this.style.height = 'auto';
  this.style.height = Math.min(this.scrollHeight, 100) + 'px';
});
document.getElementById('quiz-modal').addEventListener('click', function(e) {
  if (e.target === this) closeQuiz();
});

loadElectionData();
