const STEPS = ['received', 'parsing', 'fetching', 'analyzing', 'creating_pr'];
const STEP_LABELS = { received: '수신됨', parsing: '파싱 중', fetching: '조회 중', analyzing: '분석 중', creating_pr: '생성 중', done: '완료', failed: '실패' };

let currentErrorId = null;

// --- 유틸 ---

function esc(s) {
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}

function appendToLog(container, content, maxLines) {
  const div = document.createElement('div');
  if (typeof content === 'string') {
    div.textContent = content;
  } else {
    div.className = content.className;
    div.innerHTML = content.innerHTML;
  }
  container.appendChild(div);
  if (maxLines && container.children.length > maxLines) {
    container.removeChild(container.firstChild);
  }
  container.scrollTop = container.scrollHeight;
}

function withLoading(btn, loadingText, action) {
  const originalText = btn.textContent;
  btn.disabled = true;
  btn.textContent = loadingText;
  const restore = () => {
    btn.disabled = false;
    btn.textContent = originalText;
  };
  return action(restore);
}

// --- 파이프라인 ---

function updatePipeline(event) {
  const { error_id, step } = event;
  currentErrorId = error_id;

  document.querySelectorAll('.step').forEach(el => {
    el.classList.remove('active', 'done', 'failed');
    el.querySelector('.step-status').textContent = '대기';
  });

  if (step === 'failed') {
    document.querySelectorAll('.step').forEach(el => {
      el.classList.add('failed');
      el.querySelector('.step-status').textContent = '실패';
    });
    return;
  }

  const stepIndex = STEPS.indexOf(step === 'done' ? 'creating_pr' : step);

  STEPS.forEach((s, i) => {
    const el = document.querySelector(`.step[data-step="${s}"]`);
    if (i < stepIndex) {
      el.classList.add('done');
      el.querySelector('.step-status').textContent = '완료';
    } else if (i === stepIndex) {
      if (step === 'done') {
        el.classList.add('done');
        el.querySelector('.step-status').textContent = '완료';
      } else {
        el.classList.add('active');
        el.querySelector('.step-status').textContent = STEP_LABELS[s] || '진행 중';
      }
    }
  });
}

// --- 히스토리 ---

function renderHistory(errors) {
  const tbody = document.getElementById('historyBody');
  if (!errors.length) {
    tbody.innerHTML = '<tr><td colspan="5" class="empty-msg">에러 기록이 없습니다</td></tr>';
    return;
  }
  tbody.innerHTML = errors.map(e => {
    const time = new Date(e.timestamp).toLocaleString('ko-KR', { hour12: false });
    const badgeClass = e.step === 'done' ? 'done' : e.step === 'failed' ? 'failed' : 'active';
    const statusText = STEP_LABELS[e.step] || e.step;
    const d = e.data || {};
    const errorType = d.errorType || e.error_id || '-';
    const errorMsg = d.errorMessage ? (d.errorMessage.length > 40 ? d.errorMessage.slice(0, 40) + '...' : d.errorMessage) : '-';
    const link = d.pr_url
      ? `<a href="${d.pr_url}" target="_blank" onclick="event.stopPropagation()">PR 보기</a>`
      : '-';
    return `<tr data-eid="${e.error_id}" onclick="openModal('${e.error_id}')">
      <td>${time}</td>
      <td>${errorType}</td>
      <td>${errorMsg}</td>
      <td><span class="badge ${badgeClass}">${statusText}</span></td>
      <td>${link}</td>
    </tr>`;
  }).join('');
}

// --- 모달 ---

function openModal(errorId) {
  fetch('/api/errors/' + errorId)
    .then(r => { if (!r.ok) throw new Error('not found'); return r.json(); })
    .then(e => {
      const d = e.data || {};
      document.getElementById('modalTitle').textContent = d.errorType || e.error_id;
      let html = '';
      if (d.errorMessage) html += section('메시지', `<p>${esc(d.errorMessage)}</p>`);
      if (d.requestUrl) html += section('요청 URL', `<p>${esc(d.requestUrl)}</p>`);
      if (d.stackTrace) html += section('스택트레이스', `<pre>${esc(d.stackTrace)}</pre>`);
      if (d.root_cause) html += section('근본 원인', `<p>${esc(d.root_cause)}</p>`);
      if (d.analysis) html += section('AI 분석', `<p>${esc(d.analysis)}</p>`);
      if (d.fix_description) html += section('수정 내용', `<p>${esc(d.fix_description)}</p>`);
      if (d.pr_url) html += section('PR', `<p><a href="${d.pr_url}" target="_blank">${d.pr_url}</a></p>`);
      if (!html) html = '<p style="color:var(--text-muted);">상세 정보가 없습니다.</p>';
      document.getElementById('modalBody').innerHTML = html;
      document.getElementById('modalOverlay').classList.add('open');
    })
    .catch(() => {});
}

function closeModal() {
  document.getElementById('modalOverlay').classList.remove('open');
}

document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });
document.getElementById('modalOverlay').addEventListener('click', e => {
  if (e.target === e.currentTarget) closeModal();
});

function section(title, content) {
  return `<div class="detail-section"><h4>${title}</h4>${content}</div>`;
}

// --- 실시간 로그 ---

const logArea = document.getElementById('logArea');

function appendLog(event) {
  const ts = new Date(event.timestamp).toLocaleTimeString('ko-KR', { hour12: false });
  appendToLog(logArea, {
    className: `log-line step-${event.step}`,
    innerHTML: `<span class="ts">[${ts}]</span> <span class="msg">[${event.error_id}] ${event.message}</span>`
  }, 200);
}

// --- SSE ---

function connectSSE() {
  const es = new EventSource('/api/events');
  const dot = document.getElementById('connDot');
  const text = document.getElementById('connText');

  es.onopen = () => {
    dot.classList.add('connected');
    text.textContent = '연결됨';
  };
  es.onmessage = (e) => {
    const event = JSON.parse(e.data);
    updatePipeline(event);
    appendLog(event);
    fetch('/api/errors').then(r => r.json()).then(renderHistory);
  };
  es.onerror = () => {
    dot.classList.remove('connected');
    text.textContent = '재연결 중...';
  };
}

// --- 소스 모드 전환 ---

function setSourceMode(mode) {
  fetch('/api/source-mode', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ source_mode: mode }),
  })
    .then(r => {
      if (!r.ok) return r.json().then(d => { alert(d.detail); throw new Error(); });
      return r.json();
    })
    .then(() => updateModeButtons(mode))
    .catch(() => {});
}

function updateModeButtons(mode) {
  document.getElementById('modeGithub').classList.toggle('active', mode === 'github');
  document.getElementById('modeLocal').classList.toggle('active', mode === 'local');
}

function loadSourceMode() {
  fetch('/api/source-mode').then(r => r.json()).then(d => updateModeButtons(d.source_mode)).catch(() => {});
}

// --- 테스트 에러 전송 ---

function sendTest() {
  const btn = document.getElementById('testBtn');
  withLoading(btn, '전송 중...', (restore) => {
    fetch('/api/test-webhook', { method: 'POST' })
      .finally(() => setTimeout(restore, 3000));
  });
}

// --- 탭 ---

function switchTab(name) {
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  document.querySelector(`.tab-btn[onclick="switchTab('${name}')"]`).classList.add('active');
  document.getElementById('tab-' + name).classList.add('active');
}

// --- 테스트 코드 실행 ---

function runTests() {
  const btn = document.getElementById('runTestsBtn');
  withLoading(btn, '실행 중...', (restore) => {
    const testLog = document.getElementById('testLogArea');
    const tbody = document.getElementById('testResultsBody');
    testLog.innerHTML = '';
    tbody.innerHTML = '';
    document.getElementById('testTotal').textContent = '전체: -';
    document.getElementById('testPass').textContent = '통과: -';
    document.getElementById('testFail').textContent = '실패: -';

    const es = new EventSource('/api/tests/stream');
    es.onmessage = (e) => {
      const ev = JSON.parse(e.data);
      if (ev.type === 'log') {
        appendToLog(testLog, ev.line);
      } else if (ev.type === 'result') {
        const cls = ev.status === 'passed' ? 'done' : 'failed';
        const label = ev.status === 'passed' ? 'PASS' : ev.status.toUpperCase();
        tbody.insertAdjacentHTML('beforeend',
          `<tr><td>${esc(ev.file)}</td><td>${esc(ev.name)}</td><td><span class="badge ${cls}">${label}</span></td></tr>`);
      } else if (ev.type === 'summary') {
        document.getElementById('testTotal').textContent = '전체: ' + ev.total;
        document.getElementById('testPass').textContent = '통과: ' + ev.passed;
        document.getElementById('testFail').textContent = '실패: ' + (ev.failed + ev.error);
        es.close();
        restore();
      } else if (ev.type === 'error') {
        appendToLog(testLog, `<div style="color:var(--color-red);">${esc(ev.message)}</div>`);
        es.close();
        restore();
      }
    };
    es.onerror = () => {
      es.close();
      restore();
    };
  });
}

// --- 헬스체크 ---

function checkHealth() {
  fetch('/health')
    .then(r => r.json())
    .then(data => {
      for (const [name, info] of Object.entries(data.services || {})) {
        const el = document.getElementById('svc-' + name);
        if (!el) continue;
        const dot = el.querySelector('.status-dot');
        dot.className = 'status-dot ' + info.status;
        const old = el.querySelector('.svc-detail');
        if (old) old.remove();
        if (info.status === 'error' && info.detail) {
          const span = document.createElement('span');
          span.className = 'svc-detail';
          span.textContent = info.detail.length > 30 ? info.detail.slice(0, 30) + '...' : info.detail;
          el.appendChild(span);
        }
      }
    })
    .catch(() => {});
}

// --- 초기화 ---

fetch('/api/errors').then(r => r.json()).then(renderHistory);
connectSSE();
checkHealth();
setInterval(checkHealth, 60000);
loadSourceMode();
