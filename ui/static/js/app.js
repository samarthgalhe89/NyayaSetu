/**
 * NyayaSetu — Frontend Application Logic (Redesigned)
 *
 * Architecture:
 *   1.  State Management
 *   2.  DOM References
 *   3.  Particle Background
 *   4.  Sidebar (collapse, mobile, chat history)
 *   5.  Sources Panel
 *   6.  Chat Session Management (localStorage)
 *   7.  Landing → Chat Transition
 *   8.  API Communication
 *   9.  RAG Pipeline Animation
 *  10.  Message Rendering
 *  11.  Response Card Builder
 *  12.  Sources Panel Population
 *  13.  Input Dock (textarea, char counter)
 *  14.  Context Menu (rename, pin, delete)
 *  15.  Rename Modal
 *  16.  Event Listeners
 *  17.  Initialization
 *
 * API Endpoints (preserved, never changed):
 *   POST /api/query      → Main Q&A
 *   GET  /api/categories → Category list
 *   GET  /api/health     → Health check
 */


/* ═══════════════════════════════════════════════════════════
   1. STATE MANAGEMENT
   ═══════════════════════════════════════════════════════════ */

const STATE = {
  activeCategory: 'all',
  isLoading: false,
  sessions: [],           // All chat sessions (stored in localStorage)
  currentSessionId: null, // Active session ID
  lastSources: [],        // Sources from last response
  sidebarCollapsed: false,
  sourcesPanelOpen: true,
  contextMenuTarget: null,// Chat item the context menu is for
};

const STORAGE_KEY = 'nyayasetu_sessions';
const MAX_SESSIONS = 50;


/* ═══════════════════════════════════════════════════════════
   2. DOM REFERENCES
   ═══════════════════════════════════════════════════════════ */

const $  = (sel, ctx = document) => ctx.querySelector(sel);
const $$ = (sel, ctx = document) => [...ctx.querySelectorAll(sel)];

const dom = {
  // Layout
  sidebar:            $('#sidebar'),
  sidebarCollapseBtn: $('#sidebar-collapse-btn'),
  sidebarOpenBtn:     $('#sidebar-open-btn'),
  sidebarOverlay:     $('#sidebar-overlay'),
  sourcesPanel:       $('#sources-panel'),
  sourcesToggleBtn:   $('#sources-toggle-btn'),
  sourcesCloseBtn:    $('#sources-close-btn'),
  topbar:             $('#topbar'),

  // Sidebar content
  newChatBtn:         $('#new-chat-btn'),
  chatSearchInput:    $('#chat-search-input'),
  chatHistory:        $('#chat-history'),
  pinnedChats:        $('#pinned-chats'),
  pinnedSection:      $('#pinned-section'),
  sidebarCats:        $$('.sidebar-cat-item'),

  // Landing
  landingHero:        $('#landing-hero'),
  suggestions:        $('#suggestions'),
  heroCatChips:       $$('.hero-cat-chip'),

  // Chat
  chatArea:           $('#chat-area'),
  chatContainer:      $('#chat-container'),
  ragPipeline:        $('#rag-pipeline'),
  ragStages:          $$('.rag-stage'),

  // Input
  queryForm:          $('#query-form'),
  queryInput:         $('#query-input'),
  sendBtn:            $('#send-btn'),
  voiceBtn:           $('#voice-btn'),
  charCounter:        $('#char-counter'),

  // Sources panel
  confidenceSection:  $('#confidence-section'),
  confidenceValue:    $('#confidence-value'),
  confidenceBarFill:  $('#confidence-bar-fill'),
  categoryBadgeWrap:  $('#category-badge-wrap'),
  categoryBadgeText:  $('#category-badge-text'),
  sourcesList:        $('#sources-list'),
  sourcesEmpty:       $('#sources-empty'),
  sourcesFooter:      $('#sources-footer'),
  copyAllCitationsBtn: $('#copy-all-citations-btn'),

  // Context menu
  contextMenu:        $('#context-menu'),
  ctxRename:          $('#ctx-rename'),
  ctxPin:             $('#ctx-pin'),
  ctxDelete:          $('#ctx-delete'),

  // Rename modal
  renameModalOverlay: $('#rename-modal-overlay'),
  renameInput:        $('#rename-input'),
  renameCancelBtn:    $('#rename-cancel-btn'),
  renameConfirmBtn:   $('#rename-confirm-btn'),
};


/* ═══════════════════════════════════════════════════════════
   3. PARTICLE BACKGROUND
   ═══════════════════════════════════════════════════════════ */

function initParticles() {
  const canvas = $('#particle-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  let particles = [];
  const PARTICLE_COUNT = 60;

  function resize() {
    canvas.width  = window.innerWidth;
    canvas.height = window.innerHeight;
  }

  function createParticle() {
    return {
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 0.2,
      vy: (Math.random() - 0.5) * 0.2,
      radius: Math.random() * 1.5 + 0.3,
      alpha: Math.random() * 0.4 + 0.05,
    };
  }

  function init() {
    resize();
    particles = Array.from({ length: PARTICLE_COUNT }, createParticle);
  }

  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    particles.forEach(p => {
      p.x += p.vx;
      p.y += p.vy;

      if (p.x < 0) p.x = canvas.width;
      if (p.x > canvas.width) p.x = 0;
      if (p.y < 0) p.y = canvas.height;
      if (p.y > canvas.height) p.y = 0;

      ctx.beginPath();
      ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(201, 124, 61, ${p.alpha})`;
      ctx.fill();
    });

    requestAnimationFrame(draw);
  }

  init();
  draw();
  window.addEventListener('resize', resize, { passive: true });
}


/* ═══════════════════════════════════════════════════════════
   4. SIDEBAR
   ═══════════════════════════════════════════════════════════ */

function toggleSidebar() {
  STATE.sidebarCollapsed = !STATE.sidebarCollapsed;
  dom.sidebar.classList.toggle('collapsed', STATE.sidebarCollapsed);

  // Update aria / icon
  const icon = STATE.sidebarCollapsed ? 'panel-left-open' : 'panel-left-close';
  const label = STATE.sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar';
  dom.sidebarCollapseBtn.setAttribute('aria-label', label);
  dom.sidebarCollapseBtn.innerHTML = `<i data-lucide="${icon}"></i>`;
  lucide.createIcons({ nodes: [dom.sidebarCollapseBtn] });
}

function openMobileSidebar() {
  dom.sidebar.classList.add('mobile-open');
  dom.sidebarOverlay.classList.remove('hidden');
}

function closeMobileSidebar() {
  dom.sidebar.classList.remove('mobile-open');
  dom.sidebarOverlay.classList.add('hidden');
}

function toggleSourcesPanel() {
  if (STATE.sourcesPanelOpen) {
    closeSourcesPanel();
  } else {
    openSourcesPanel();
  }
}

function openSourcesPanel() {
  STATE.sourcesPanelOpen = true;
  dom.sourcesPanel.classList.remove('hidden-panel');
  dom.sourcesToggleBtn.style.display = "none";
  if (window.innerWidth <= 1024) {
    dom.sourcesPanel.classList.add('mobile-open');
  }
}

function closeSourcesPanel() {
    console.log("Closing panel clicked!");

    STATE.sourcesPanelOpen = false;

    console.log(dom.sourcesPanel);

    dom.sourcesPanel.classList.add("hidden-panel");

    dom.sourcesToggleBtn.style.display = "flex";
}


/* ═══════════════════════════════════════════════════════════
   5. CHAT SESSION MANAGEMENT
   ═══════════════════════════════════════════════════════════ */

function loadSessions() {
  try {
    STATE.sessions = JSON.parse(localStorage.getItem(STORAGE_KEY)) || [];
  } catch {
    STATE.sessions = [];
  }
}

function saveSessions() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(STATE.sessions.slice(0, MAX_SESSIONS)));
  } catch { /* quota exceeded */ }
}

function createSession(firstQuestion) {
  const session = {
    id: `s_${Date.now()}`,
    name: firstQuestion.slice(0, 50),
    createdAt: Date.now(),
    updatedAt: Date.now(),
    pinned: false,
    category: STATE.activeCategory,
    messages: [],
  };
  STATE.sessions.unshift(session);
  STATE.currentSessionId = session.id;
  saveSessions();
  renderChatHistory();
  return session;
}

function getCurrentSession() {
  return STATE.sessions.find(s => s.id === STATE.currentSessionId) || null;
}

function updateSessionName(id, name) {
  const session = STATE.sessions.find(s => s.id === id);
  if (session) {
    session.name = name;
    session.updatedAt = Date.now();
    saveSessions();
    renderChatHistory();
  }
}

function togglePinSession(id) {
  const session = STATE.sessions.find(s => s.id === id);
  if (session) {
    session.pinned = !session.pinned;
    saveSessions();
    renderChatHistory();
  }
}

function deleteSession(id) {
  STATE.sessions = STATE.sessions.filter(s => s.id !== id);
  if (STATE.currentSessionId === id) {
    STATE.currentSessionId = null;
    startNewChat();
  }
  saveSessions();
  renderChatHistory();
}

function addMessageToSession(role, content, sources = []) {
  const session = getCurrentSession();
  if (!session) return;
  session.messages.push({ role, content, sources, timestamp: Date.now() });
  session.updatedAt = Date.now();
  saveSessions();
}

/* Render sidebar history */
function renderChatHistory(filter = '') {
  const pinned   = STATE.sessions.filter(s => s.pinned);
  const unpinned = STATE.sessions.filter(s => !s.pinned);

  const filterLow = filter.toLowerCase();

  function matchesFilter(s) {
    return !filter || s.name.toLowerCase().includes(filterLow);
  }

  function buildItem(session) {
    const div = document.createElement('div');
    div.className = `chat-history-item${session.id === STATE.currentSessionId ? ' active' : ''}`;
    div.setAttribute('data-id', session.id);
    div.setAttribute('role', 'button');
    div.setAttribute('tabindex', '0');
    div.setAttribute('aria-label', `Open chat: ${session.name}`);

    div.innerHTML = `
      <i data-lucide="message-square"></i>
      <span class="chat-history-item-name" title="${escapeHtml(session.name)}">${escapeHtml(session.name)}</span>
      <button class="chat-history-item-menu" aria-label="Chat options" data-id="${session.id}">
        <i data-lucide="more-horizontal"></i>
      </button>
    `;

    div.addEventListener('click', (e) => {
      if (e.target.closest('.chat-history-item-menu')) return;
      loadSession(session.id);
    });

    div.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') loadSession(session.id);
    });

    const menuBtn = div.querySelector('.chat-history-item-menu');
    menuBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      showContextMenu(e, session.id);
    });

    return div;
  }

  // Pinned
  dom.pinnedChats.innerHTML = '';
  pinned.filter(matchesFilter).forEach(s => {
    dom.pinnedChats.appendChild(buildItem(s));
  });
  dom.pinnedSection.style.display = pinned.filter(matchesFilter).length ? '' : 'none';

  // Unpinned
  dom.chatHistory.innerHTML = '';
  const filteredUnpinned = unpinned.filter(matchesFilter);
  
  if (filteredUnpinned.length === 0) {
    const emptyState = document.createElement('div');
    emptyState.style.padding = 'var(--s-4) var(--s-3)';
    emptyState.style.color = 'var(--text-muted)';
    emptyState.style.fontSize = '0.85rem';
    emptyState.style.fontStyle = 'italic';
    emptyState.style.textAlign = 'center';
    emptyState.textContent = 'Nothing here yet. Start a new chat!';
    dom.chatHistory.appendChild(emptyState);
  } else {
    filteredUnpinned.forEach(s => {
      dom.chatHistory.appendChild(buildItem(s));
    });
  }

  lucide.createIcons({ nodes: [dom.pinnedChats, dom.chatHistory] });
}


/* Load a previous session */
function loadSession(id) {
  const session = STATE.sessions.find(s => s.id === id);
  if (!session) return;

  STATE.currentSessionId = id;
  STATE.activeCategory = session.category || 'all';

  // Highlight active category
  dom.sidebarCats.forEach(c => c.classList.toggle('active', c.dataset.category === STATE.activeCategory));

  // Switch to chat view
  dom.landingHero.classList.add('hidden');
  dom.chatArea.classList.remove('hidden');

  // Render all messages
  dom.chatContainer.innerHTML = '';
  session.messages.forEach(msg => {
    if (msg.role === 'user') {
      appendUserMessage(msg.content, msg.timestamp);
    } else if (msg.role === 'bot') {
      appendBotMessage(msg.content, msg.sources || [], msg.timestamp, false);
    }
  });

  // Update sources panel with last bot message's sources
  const lastBot = [...session.messages].reverse().find(m => m.role === 'bot');
  if (lastBot && lastBot.sources && lastBot.sources.length > 0) {
    populateSourcesPanel(lastBot.sources, null, session.category);
  } else {
    clearSourcesPanel();
  }

  scrollToBottom();
  renderChatHistory();
  closeMobileSidebar();
}


/* Start a brand new chat */
function startNewChat() {
  STATE.currentSessionId = null;
  dom.chatContainer.innerHTML = '';
  dom.chatArea.classList.add('hidden');
  dom.landingHero.classList.remove('hidden');
  clearSourcesPanel();
  renderChatHistory();
  dom.queryInput.focus();
  closeMobileSidebar();
}


/* ═══════════════════════════════════════════════════════════
   6. API COMMUNICATION
   ═══════════════════════════════════════════════════════════ */

/**
 * POST /api/query — ask a legal question, get structured answer + sources + confidence.
 */
async function queryAPI(question, category = null) {
  const body = { question };
  if (category && category !== 'all') {
    body.category = category;
  }

  const response = await fetch('/api/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Server error: ${response.status}`);
  }

  return response.json();
}


/* ═══════════════════════════════════════════════════════════
   7. RAG PIPELINE ANIMATION
   ═══════════════════════════════════════════════════════════ */

let ragTimers = [];

function showRAGPipeline() {
  dom.ragPipeline.classList.remove('hidden');
  dom.sendBtn.disabled = true;
  STATE.isLoading = true;

  // Reset stages
  dom.ragStages.forEach(s => {
    s.classList.remove('active', 'done');
  });

  const delays = [0, 700, 1400, 2200, 3200];
  const donedelays = [600, 1300, 2100, 3100, 9999]; // last one stays active until done

  delays.forEach((delay, i) => {
    const t1 = setTimeout(() => {
      dom.ragStages.forEach(s => s.classList.remove('active'));
      if (i > 0) dom.ragStages[i - 1].classList.add('done');
      dom.ragStages[i].classList.add('active');
    }, delay);
    ragTimers.push(t1);
  });
}

function hideRAGPipeline() {
  ragTimers.forEach(t => clearTimeout(t));
  ragTimers = [];

  // Flash all as done
  dom.ragStages.forEach(s => {
    s.classList.remove('active');
    s.classList.add('done');
  });

  setTimeout(() => {
    dom.ragPipeline.classList.add('hidden');
    dom.ragStages.forEach(s => s.classList.remove('active', 'done'));
    dom.sendBtn.disabled = false;
    STATE.isLoading = false;
  }, 400);
}


/* ═══════════════════════════════════════════════════════════
   8. MESSAGE RENDERING
   ═══════════════════════════════════════════════════════════ */

function now() {
  return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

function scrollToBottom() {
  setTimeout(() => {
    const area = dom.chatArea;
    if (area && !area.classList.contains('hidden')) {
      area.scrollTop = area.scrollHeight;
    }
  }, 50);
}

/* Append a user message bubble */
function appendUserMessage(text, timestamp) {
  const ts = timestamp ? new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : now();

  const msg = document.createElement('div');
  msg.className = 'chat-msg user';
  msg.innerHTML = `
    <div class="chat-avatar" aria-hidden="true">
      <i data-lucide="user"></i>
    </div>
    <div class="chat-bubble-wrap">
      <div class="chat-bubble">${escapeHtml(text)}</div>
      <span class="msg-timestamp">${ts}</span>
    </div>
  `;
  dom.chatContainer.appendChild(msg);
  lucide.createIcons({ nodes: [msg] });
  scrollToBottom();
}

/* Append a bot response bubble */
function appendBotMessage(answer, sources, timestamp, animate = true) {
  const ts = timestamp ? new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : now();

  const msg = document.createElement('div');
  msg.className = 'chat-msg bot';

  // Build response cards from the markdown answer
  const cardsHTML = buildResponseCards(answer);

  // Build citation badges
  let citationsHTML = '';
  if (sources && sources.length > 0) {
    const badges = sources.map((src, i) => {
      const label = src.section_number ? `Sec ${src.section_number}` : `Source ${i + 1}`;
      const actShort = (src.act_name || '').split(' ').slice(0, 3).join(' ');
      return `<button class="citation-badge" data-source-index="${i}" aria-label="View source: ${label}">
        <i data-lucide="book-marked"></i>
        ${label}${actShort ? ` · ${actShort}` : ''}
      </button>`;
    }).join('');
    citationsHTML = `<div class="citations-row">${badges}</div>`;
  }

  msg.innerHTML = `
    <div class="chat-avatar" aria-hidden="true">
      <i data-lucide="scale"></i>
    </div>
    <div class="chat-bubble-wrap">
      <div class="chat-bubble">
        ${cardsHTML}
        ${citationsHTML}
      </div>
      <span class="msg-timestamp">${ts}</span>
    </div>
  `;

  // Wire up citation badges → sources panel
  if (sources && sources.length > 0) {
    msg.querySelectorAll('.citation-badge').forEach(badge => {
      badge.addEventListener('click', () => {
        const idx = parseInt(badge.dataset.sourceIndex);
        highlightSource(idx);
        openSourcesPanel();
      });
    });

    // Response card toggle
    msg.querySelectorAll('.response-card-header').forEach(header => {
      header.addEventListener('click', () => {
        const card = header.closest('.response-card');
        card.classList.toggle('collapsed');
      });
    });
  }

  dom.chatContainer.appendChild(msg);
  lucide.createIcons({ nodes: [msg] });

  // Stagger card animations
  if (animate) {
    msg.querySelectorAll('.response-card').forEach((card, i) => {
      card.style.animationDelay = `${i * 80}ms`;
    });
  }

  scrollToBottom();
  return msg;
}

/* Append error bubble */
function appendErrorMessage(text) {
  const msg = document.createElement('div');
  msg.className = 'chat-msg error';
  msg.innerHTML = `
    <div class="chat-avatar" aria-hidden="true">
      <i data-lucide="alert-triangle"></i>
    </div>
    <div class="chat-bubble-wrap">
      <div class="chat-bubble">
        <p><strong>Error:</strong> ${escapeHtml(text)}</p>
        <p style="font-size:0.8rem;margin-top:8px;color:var(--text-muted)">Please try again or rephrase your question.</p>
      </div>
      <span class="msg-timestamp">${now()}</span>
    </div>
  `;
  dom.chatContainer.appendChild(msg);
  lucide.createIcons({ nodes: [msg] });
  scrollToBottom();
}


/* ═══════════════════════════════════════════════════════════
   9. RESPONSE CARD BUILDER
   ═══════════════════════════════════════════════════════════ */

/**
 * Parses the LLM markdown response and converts it into structured glass cards.
 * Falls back to a single rendered markdown card if no sections detected.
 */
function buildResponseCards(markdownText) {
  // Try to detect section headers from the markdown
  const sections = extractSections(markdownText);

  if (sections.length > 1) {
    return `<div class="response-cards">${sections.map(buildCard).join('')}</div>`;
  }

  // Fallback: render as single markdown card
  const htmlContent = marked.parse(markdownText);
  return `
    <div class="response-cards">
      <div class="response-card card-summary" style="animation-delay:0ms">
        <div class="response-card-header" tabindex="0" role="button" aria-expanded="true">
          <div class="response-card-icon"><i data-lucide="zap"></i></div>
          <span class="response-card-title">Legal Analysis</span>
          <div class="response-card-chevron"><i data-lucide="chevron-down"></i></div>
        </div>
        <div class="response-card-body" style="max-height:2000px">${htmlContent}</div>
      </div>
    </div>
  `;
}

function extractSections(md) {
  const lines = md.split('\n');
  const sections = [];
  let current = null;

  for (const line of lines) {
    const headingMatch = line.match(/^#{1,3}\s+(.+)/);
    if (headingMatch) {
      if (current) sections.push(current);
      current = { title: headingMatch[1].replace(/[📋⚖️📌🔔⚠️🛡️✅❌🚨💡🏛️]/g, '').trim(), body: [] };
    } else if (current) {
      current.body.push(line);
    }
  }

  if (current) sections.push(current);
  return sections.filter(s => s.body.join('').trim().length > 0);
}

/** Map section title keywords to card style + icon */
function getCardStyle(title) {
  const t = title.toLowerCase();

  if (/summary|short answer|tldr|overview|answer/.test(t))
    return { cls: 'card-summary', icon: 'zap' };
  if (/provision|law|act|section|article|statute|legal basis|cited/.test(t))
    return { cls: 'card-provisions', icon: 'book-open' };
  if (/step|action|procedure|process|how to|file|complaint|remedy|what to do/.test(t))
    return { cls: 'card-steps', icon: 'list-checks' };
  if (/remember|note|important|key|tips|mind|aware/.test(t))
    return { cls: 'card-remember', icon: 'info' };
  if (/exception|limitation|condition|unless|however/.test(t))
    return { cls: 'card-remember', icon: 'alert-circle' };
  if (/disclaimer|warning|consult|advice|professional/.test(t))
    return { cls: 'card-disclaimer', icon: 'shield-alert' };

  return { cls: 'card-summary', icon: 'file-text' };
}

function buildCard(section, index) {
  const { cls, icon } = getCardStyle(section.title);

  const bodyClass =
      cls === "card-provisions"
          ? "response-card-body provisions-body"
          : "response-card-body";

  const bodyHtml = marked.parse(section.body.join('\n'));

  const lines = section.body.length;
  const estimatedHeight = Math.max(200, lines * 28) + "px";

  const bodyStyle =
    cls === "card-provisions"
        ? ""
        : `style="max-height:${estimatedHeight}"`;

  return `
    <div class="response-card ${cls}" style="animation-delay:${index * 80}ms">
      <div class="response-card-header" tabindex="0" role="button" aria-expanded="true">
        <div class="response-card-icon">
          <i data-lucide="${icon}"></i>
        </div>

        <span class="response-card-title">
          ${escapeHtml(section.title)}
        </span>

        <div class="response-card-chevron">
          <i data-lucide="chevron-down"></i>
        </div>
      </div>

      <div class="${bodyClass}" ${bodyStyle}>
        ${bodyHtml}
      </div>
    </div>
  `;
}


/* ═══════════════════════════════════════════════════════════
   10. SOURCES PANEL POPULATION
   ═══════════════════════════════════════════════════════════ */

function clearSourcesPanel() {
  dom.confidenceSection.classList.add('hidden');
  dom.categoryBadgeWrap.classList.add('hidden');
  dom.sourcesEmpty.classList.remove('hidden');
  dom.sourcesFooter.style.display = 'none';

  // Remove existing source cards (but not the empty state)
  $$('.source-card', dom.sourcesList).forEach(el => el.remove());
}

function populateSourcesPanel(sources, confidence, category) {
  clearSourcesPanel();

  if (!sources || sources.length === 0) return;

  STATE.lastSources = sources;

  // Confidence meter
  if (confidence != null) {
    const pct = Math.round(confidence * 100);
    dom.confidenceSection.classList.remove('hidden');
    dom.confidenceValue.textContent = `${pct}%`;
    // Trigger animation after paint
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        dom.confidenceBarFill.style.width = `${pct}%`;
      });
    });
  }

  // Category badge
  if (category && category !== 'all') {
    dom.categoryBadgeWrap.classList.remove('hidden');
    dom.categoryBadgeText.textContent = category;
  }

  // Hide empty state
  dom.sourcesEmpty.classList.add('hidden');

  // Build source cards
  sources.forEach((src, i) => {
    const card = buildSourceCard(src, i);
    dom.sourcesList.appendChild(card);
    lucide.createIcons({ nodes: [card] });
  });

  // Show footer
  dom.sourcesFooter.style.display = '';

  // Stagger animation
  $$('.source-card', dom.sourcesList).forEach((card, i) => {
    card.style.animationDelay = `${i * 80}ms`;
  });
}

function buildSourceCard(src, index) {
  const card = document.createElement('div');
  card.className = 'source-card';
  card.id = `source-card-${index}`;

  const scorePercent = Math.round((src.similarity_score || 0) * 100);
  const act = escapeHtml(src.act_name || 'Legal Document');
  const section = src.section_number ? `<span class="source-tag">Section ${escapeHtml(src.section_number)}</span>` : '';
  const sectionTitle = src.section_title ? `<span class="source-tag">${escapeHtml(src.section_title)}</span>` : '';
  const page = src.page ? `<span class="source-tag">Page ${src.page}</span>` : '';
  const preview = escapeHtml(src.preview || 'No preview available.');
  const citation = buildCitationText(src);

  card.innerHTML = `
    <div class="source-card-header">
      <div class="source-card-index">${index + 1}</div>
      <div class="source-card-act">${act}</div>
      <div class="source-card-tags">
        ${section}
        ${sectionTitle}
        ${page}
      </div>
    </div>
    <div class="source-card-preview">${preview}</div>
    <div class="source-card-footer">
      <div class="source-relevance">
        <span class="source-relevance-label">
          Relevance
          <span class="source-relevance-score">${scorePercent}%</span>
        </span>
        <div class="source-bar">
          <div class="source-bar-fill" style="width:${scorePercent}%"></div>
        </div>
      </div>
      <button class="source-copy-btn" data-citation="${escapeHtml(citation)}" aria-label="Copy citation">
        <i data-lucide="copy"></i>
        Cite
      </button>
    </div>
  `;

  card.querySelector('.source-copy-btn').addEventListener('click', (e) => {
    const text = e.currentTarget.dataset.citation;
    copyToClipboard(text, e.currentTarget);
  });

  return card;
}

function buildCitationText(src) {
  let cite = src.act_name || 'Unknown Act';
  if (src.section_number) cite += `, Section ${src.section_number}`;
  if (src.section_title)  cite += ` (${src.section_title})`;
  if (src.page)           cite += `, Page ${src.page}`;
  return cite;
}

function highlightSource(index) {
  $$('.source-card').forEach((c, i) => {
    c.style.borderColor = '';
    c.style.boxShadow  = '';
    if (i === index) {
      c.style.borderColor = 'var(--primary-500)';
      c.style.boxShadow = '0 0 20px var(--primary-glow)';
      c.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  });
}

function copyToClipboard(text, btn) {
  navigator.clipboard.writeText(text).then(() => {
    const orig = btn.innerHTML;
    btn.innerHTML = '<i data-lucide="check"></i> Copied!';
    btn.style.color = 'var(--emerald-400)';
    lucide.createIcons({ nodes: [btn] });
    setTimeout(() => {
      btn.innerHTML = orig;
      btn.style.color = '';
      lucide.createIcons({ nodes: [btn] });
    }, 2000);
  }).catch(() => {
    // Fallback
    const ta = document.createElement('textarea');
    ta.value = text;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);
  });
}


/* ═══════════════════════════════════════════════════════════
   11. MAIN QUERY FLOW
   ═══════════════════════════════════════════════════════════ */

async function handleQuery(question) {
  question = question.trim();
  if (!question || STATE.isLoading) return;

  // First message: create session + transition to chat view
  if (!STATE.currentSessionId) {
    createSession(question);
    dom.landingHero.classList.add('hidden');
    dom.chatArea.classList.remove('hidden');
  }

  // Add user message to UI + session
  appendUserMessage(question);
  addMessageToSession('user', question);
  dom.queryInput.value = '';
  dom.queryInput.style.height = 'auto';
  updateCharCounter();

  // Start RAG animation
  showRAGPipeline();
  clearSourcesPanel();

  try {
    const result = await queryAPI(question, STATE.activeCategory);
    hideRAGPipeline();

    // Render bot response
    appendBotMessage(result.answer, result.sources, Date.now(), true);
    addMessageToSession('bot', result.answer, result.sources);

    // Populate sources panel
    populateSourcesPanel(result.sources, result.confidence, result.category || STATE.activeCategory);

    // Open sources panel on desktop if it's hidden
    if (result.sources && result.sources.length > 0 && window.innerWidth > 1024) {
      openSourcesPanel();
    }

  } catch (error) {
    hideRAGPipeline();
    appendErrorMessage(error.message || 'Something went wrong. Please try again.');
    console.error('[NyayaSetu] Query error:', error);
  }

  renderChatHistory();
}


/* ═══════════════════════════════════════════════════════════
   12. INPUT DOCK
   ═══════════════════════════════════════════════════════════ */

function updateCharCounter() {
  const len = dom.queryInput.value.length;
  const max = 4000;
  dom.charCounter.textContent = `${len} / ${max}`;
  dom.charCounter.classList.toggle('warning', len > 3000 && len <= 3800);
  dom.charCounter.classList.toggle('danger', len > 3800);
}

function autoResizeTextarea() {
  const ta = dom.queryInput;
  ta.style.height = 'auto';
  ta.style.height = Math.min(ta.scrollHeight, 160) + 'px';
}


/* ═══════════════════════════════════════════════════════════
   13. CONTEXT MENU (rename, pin, delete)
   ═══════════════════════════════════════════════════════════ */

function showContextMenu(e, sessionId) {
  e.stopPropagation();
  STATE.contextMenuTarget = sessionId;

  const menu = dom.contextMenu;
  menu.classList.remove('hidden');

  // Position relative to cursor / button
  const rect = e.currentTarget.getBoundingClientRect();
  let top = rect.bottom + 4;
  let left = rect.left;

  // Keep on screen
  if (left + 180 > window.innerWidth) left = window.innerWidth - 185;
  if (top + 140 > window.innerHeight) top = rect.top - 144;

  menu.style.top  = `${top}px`;
  menu.style.left = `${left}px`;

  // Update pin label
  const session = STATE.sessions.find(s => s.id === sessionId);
  if (session) {
    dom.ctxPin.innerHTML = `<i data-lucide="${session.pinned ? 'pin-off' : 'pin'}"></i> ${session.pinned ? 'Unpin' : 'Pin'}`;
    lucide.createIcons({ nodes: [dom.ctxPin] });
  }
}

function hideContextMenu() {
  dom.contextMenu.classList.add('hidden');
  STATE.contextMenuTarget = null;
}

function openRenameModal() {
  const session = STATE.sessions.find(s => s.id === STATE.contextMenuTarget);
  if (!session) return;
  dom.renameInput.value = session.name;
  dom.renameModalOverlay.classList.remove('hidden');
  dom.renameModalOverlay.removeAttribute('aria-hidden');
  dom.renameInput.focus();
  dom.renameInput.select();
}

function closeRenameModal() {
  dom.renameModalOverlay.classList.add('hidden');
  dom.renameModalOverlay.setAttribute('aria-hidden', 'true');
}

function confirmRename() {
  const newName = dom.renameInput.value.trim();
  if (newName && STATE.contextMenuTarget) {
    updateSessionName(STATE.contextMenuTarget, newName);
  }
  closeRenameModal();
}


/* ═══════════════════════════════════════════════════════════
   14. COPY ALL CITATIONS
   ═══════════════════════════════════════════════════════════ */

function copyAllCitations() {
  if (!STATE.lastSources.length) return;
  const text = STATE.lastSources.map((src, i) => `[${i + 1}] ${buildCitationText(src)}`).join('\n');
  copyToClipboard(text, dom.copyAllCitationsBtn);
}


/* ═══════════════════════════════════════════════════════════
   15. CATEGORY SELECTION
   ═══════════════════════════════════════════════════════════ */

function setActiveCategory(cat) {
  STATE.activeCategory = cat;
  dom.sidebarCats.forEach(btn => btn.classList.toggle('active', btn.dataset.category === cat));
  dom.heroCatChips.forEach(chip => chip.classList.toggle('active', chip.dataset.category === cat));
}


/* ═══════════════════════════════════════════════════════════
   16. EVENT LISTENERS
   ═══════════════════════════════════════════════════════════ */

function bindEvents() {

  console.log(dom);

  // ── Sidebar ──
  if (dom.sidebarCollapseBtn) {
    dom.sidebarCollapseBtn.addEventListener('click', toggleSidebar);
  }
  dom.sidebarOpenBtn.addEventListener('click', openMobileSidebar);
  dom.sidebarOverlay.addEventListener('click', closeMobileSidebar);

  // ── Sources panel ──
  if (dom.sourcesToggleBtn) {
      dom.sourcesToggleBtn.addEventListener("click", toggleSourcesPanel);
  }

  if (dom.sourcesCloseBtn) {
      dom.sourcesCloseBtn.addEventListener("click", closeSourcesPanel);
  }

  // ── New chat ──
  dom.newChatBtn.addEventListener('click', startNewChat);

  // ── Chat search ──
  dom.chatSearchInput.addEventListener('input', () => {
    renderChatHistory(dom.chatSearchInput.value);
  });

  // ── Sidebar categories ──
  dom.sidebarCats.forEach(btn => {
    btn.addEventListener('click', () => setActiveCategory(btn.dataset.category));
  });

  // ── Hero category chips ──
  dom.heroCatChips.forEach(chip => {
    chip.addEventListener('click', () => setActiveCategory(chip.dataset.category));
  });

  // ── Suggestion cards ──
  $$('.suggestion-item').forEach(card => {
    card.addEventListener('click', () => {
      dom.queryInput.value = card.dataset.question;
      autoResizeTextarea();
      updateCharCounter();
      dom.queryInput.focus();
    });
  });

  // ── Form submit ──
  dom.queryForm.addEventListener('submit', (e) => {
    e.preventDefault();
    handleQuery(dom.queryInput.value);
  });

  // ── Textarea auto-resize + counter ──
  dom.queryInput.addEventListener('input', () => {
    autoResizeTextarea();
    updateCharCounter();
  });

  // ── Enter to submit (Shift+Enter = new line) ──
  dom.queryInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleQuery(dom.queryInput.value);
    }
  });

  // ── Voice button (UI stub — visual feedback) ──
  if (dom.voiceBtn) {
  dom.voiceBtn.addEventListener('click', () => {
    dom.voiceBtn.classList.toggle('listening');

    if (dom.voiceBtn.classList.contains('listening')) {
      dom.queryInput.placeholder = 'Listening...';

      if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SR();
        recognition.lang = 'en-IN';
        recognition.interimResults = false;
        recognition.onresult = (event) => {
          dom.queryInput.value = event.results[0][0].transcript;
          autoResizeTextarea();
          updateCharCounter();
          dom.voiceBtn.classList.remove('listening');
          dom.queryInput.placeholder = 'Ask your legal question...';
        };
        recognition.onerror = () => {
          dom.voiceBtn.classList.remove('listening');
          dom.queryInput.placeholder = 'Ask your legal question...';
        };
        recognition.onend = () => {
          dom.voiceBtn.classList.remove('listening');
          dom.queryInput.placeholder = 'Ask your legal question...';
        };
        recognition.start();
      } else {
        setTimeout(() => {
          dom.voiceBtn.classList.remove('listening');
          dom.queryInput.placeholder = 'Ask your legal question...';
        }, 2000);
      }
    } else {
      dom.queryInput.placeholder = 'Ask your legal question...';
    }
  });
} 

  // ── Context menu actions ──
  dom.ctxRename.addEventListener('click', () => {
    hideContextMenu();
    openRenameModal();
  });

  dom.ctxPin.addEventListener('click', () => {
    if (STATE.contextMenuTarget) togglePinSession(STATE.contextMenuTarget);
    hideContextMenu();
  });

  dom.ctxDelete.addEventListener('click', () => {
    if (STATE.contextMenuTarget) deleteSession(STATE.contextMenuTarget);
    hideContextMenu();
  });

  // Hide context menu on outside click
  document.addEventListener('click', (e) => {
    if (!dom.contextMenu.contains(e.target)) {
      hideContextMenu();
    }
  });

  // ── Rename modal ──
  dom.renameCancelBtn.addEventListener('click', closeRenameModal);
  dom.renameConfirmBtn.addEventListener('click', confirmRename);
  dom.renameInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') confirmRename();
    if (e.key === 'Escape') closeRenameModal();
  });
  dom.renameModalOverlay.addEventListener('click', (e) => {
    if (e.target === dom.renameModalOverlay) closeRenameModal();
  });

  // ── Copy all citations ──
  dom.copyAllCitationsBtn.addEventListener('click', copyAllCitations);

  // ── Footer buttons (non-functional stubs — visual) ──
  $('#about-btn').addEventListener('click', () => {
    const text = 'NyayaSetu is an AI-powered legal rights navigator for Indian citizens. Built with FastAPI, LangChain, ChromaDB, SentenceTransformers, and Groq Llama 3.1.';
    alert(text);
  });

  // ── Keyboard shortcuts ──
  document.addEventListener('keydown', (e) => {
    // Escape closes modals / panels
    if (e.key === 'Escape') {
      if (!dom.renameModalOverlay.classList.contains('hidden')) {
        closeRenameModal();
      }
      hideContextMenu();
    }

    // Ctrl/Cmd + K → focus input
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
      e.preventDefault();
      dom.queryInput.focus();
    }

    // Ctrl/Cmd + N → new chat
    if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
      e.preventDefault();
      startNewChat();
    }
  });

  // ── Response card toggle (delegated) ──
  dom.chatContainer.addEventListener('click', (e) => {
    const header = e.target.closest('.response-card-header');
    if (header) {
      const card = header.closest('.response-card');
      const body = card.querySelector('.response-card-body');
      card.classList.toggle('collapsed');
      header.setAttribute('aria-expanded', !card.classList.contains('collapsed'));
    }
  });
}


/* ═══════════════════════════════════════════════════════════
   17. INITIALIZATION
   ═══════════════════════════════════════════════════════════ */

function init() {
  // Load sessions from localStorage
  loadSessions();

  // Init particles
  initParticles();

  // Render chat history sidebar
  renderChatHistory();

  // Bind all events
  bindEvents();

  // Focus input
  dom.queryInput.focus();

  // Re-render Lucide icons (the HTML already calls lucide.createIcons after load)
  // This handles any dynamically created icons on page load

  console.log('[NyayaSetu] App initialized. Backend API: /api/query, /api/health, /api/categories');
}

// Wait for DOM and Lucide to be ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
