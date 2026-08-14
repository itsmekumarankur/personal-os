const STORAGE_KEY = 'action_machine_tasks_v1';

let tasks = loadTasks();
let timers = {}; // id -> intervalId

function loadTasks() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      parsed.forEach(t => t.active = false);
      return parsed;
    }
  } catch (e) {}
  return [
    { id: 1, name: 'Deep work', duration: 60, remaining: 60 * 60, active: false, done: false },
    { id: 2, name: 'Team review', duration: 45, remaining: 45 * 60, active: false, done: false },
    { id: 3, name: 'Learning block', duration: 90, remaining: 90 * 60, active: false, done: false }
  ];
}

function saveTasks() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(tasks));
}

function addTask() {
  const input = document.getElementById('taskInput');
  const name = input.value.trim();
  if (!name) return;
  const dur = 60;
  tasks.push({ id: Date.now(), name, duration: dur, remaining: dur * 60, active: false, done: false });
  input.value = '';
  saveTasks();
  render();
}

function deleteTask(id) {
  stopTimer(id);
  tasks = tasks.filter(t => t.id !== id);
  saveTasks();
  render();
}

function toggleTask(id) {
  const task = tasks.find(t => t.id === id);
  if (!task || task.done) return;
  if (task.active) {
    stopTimer(id);
    task.active = false;
  } else {
    tasks.forEach(t => { if (t.active) { stopTimer(t.id); t.active = false; } });
    task.active = true;
    startTimer(id);
  }
  saveTasks();
  render();
}

function markDone(id) {
  const task = tasks.find(t => t.id === id);
  if (!task) return;
  stopTimer(id);
  task.active = false;
  task.done = true;
  playDing();
  saveTasks();
  render();
}

function reopenTask(id) {
  const task = tasks.find(t => t.id === id);
  if (!task) return;
  task.done = false;
  saveTasks();
  render();
}

function startTimer(id) {
  stopTimer(id);
  timers[id] = setInterval(() => {
    const task = tasks.find(t => t.id === id);
    if (!task) { stopTimer(id); return; }
    if (task.remaining > 0) {
      task.remaining -= 1;
      saveTasks();
      updateBlockDisplay(id);
    } else {
      stopTimer(id);
      task.active = false;
      task.done = true;
      playDing();
      saveTasks();
      render();
    }
  }, 1000);
}

function stopTimer(id) {
  if (timers[id]) {
    clearInterval(timers[id]);
    delete timers[id];
  }
}

function updateDuration(id, minutes) {
  const task = tasks.find(t => t.id === id);
  if (!task) return;
  task.duration = parseInt(minutes);
  if (!task.active) task.remaining = task.duration * 60;
  saveTasks();
  render();
}

function playDing() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const o = ctx.createOscillator();
    const g = ctx.createGain();
    o.connect(g); g.connect(ctx.destination);
    o.frequency.value = 880;
    g.gain.setValueAtTime(0.2, ctx.currentTime);
    o.start();
    o.frequency.exponentialRampToValueAtTime(440, ctx.currentTime + 0.4);
    g.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.6);
    o.stop(ctx.currentTime + 0.6);
  } catch (e) {}
}

function formatTime(sec) {
  const m = Math.floor(sec / 60).toString().padStart(2, '0');
  const s = (sec % 60).toString().padStart(2, '0');
  return m + ':' + s;
}

function updateBlockDisplay(id) {
  const task = tasks.find(t => t.id === id);
  if (!task) return;
  const timeEl = document.getElementById('time-' + id);
  const fillEl = document.getElementById('fill-' + id);
  if (timeEl) timeEl.textContent = formatTime(task.remaining);
  if (fillEl) {
    const total = task.duration * 60;
    const pct = total > 0 ? ((total - task.remaining) / total) * 100 : 0;
    fillEl.style.width = pct + '%';
  }
}

function render() {
  const totalMin = tasks.reduce((s, t) => s + t.duration, 0);
  document.getElementById('dayStats').textContent = `${tasks.length} tasks • ${totalMin} min planned`;

  const taskList = document.getElementById('taskList');
  if (tasks.length === 0) {
    taskList.innerHTML = '<div class="empty-state">No tasks yet.<br>Add your first one above.</div>';
  } else {
    taskList.innerHTML = tasks.map(t => `
      <div class="task-item ${t.active ? 'active' : ''} ${t.done ? 'done' : ''}" onclick="${t.done ? `reopenTask(${t.id})` : `toggleTask(${t.id})`}">
        <span class="task-name">${t.active ? '🔥 ' : (t.done ? '✅ ' : '')}${escapeHtml(t.name)}</span>
        <button class="delete-btn" onclick="event.stopPropagation(); deleteTask(${t.id})"><i class="fas fa-trash-alt"></i></button>
      </div>
    `).join('');
  }

  const grid = document.getElementById('tasksGrid');
  if (tasks.length === 0) {
    grid.innerHTML = '<div class="empty-state">Nothing to show. Add a task on the left.</div>';
  } else {
    grid.innerHTML = tasks.map(t => {
      const total = t.duration * 60;
      const pct = total > 0 ? ((total - t.remaining) / total) * 100 : 0;
      return `
      <div class="task-block ${t.active ? 'burning' : ''} ${t.done ? 'done' : ''}">
        <div class="task-block-title">
          ${t.done ? '✅' : ''}
          ${escapeHtml(t.name)}
        </div>
        ${t.active ? `
        <div class="flame-wrap">
          <div class="flame"></div><div class="flame"></div><div class="flame"></div><div class="flame"></div>
        </div>` : ''}
        <div class="time-display ${t.active ? 'burning' : ''}" id="time-${t.id}">${t.done ? 'Done' : formatTime(t.remaining)}</div>
        <div class="duration-display">Total: ${t.duration} min</div>
        <div class="progress-bar"><div class="progress-fill" id="fill-${t.id}" style="width:${pct}%"></div></div>
        <div class="duration-label">Duration (min)</div>
        <input type="range" class="duration-slider" min="5" max="180" step="5"
          value="${t.duration}" ${(t.active || t.done) ? 'disabled' : ''}
          onchange="updateDuration(${t.id}, this.value)">
        <div class="controls">
          ${t.done ? `
            <button class="control-btn" onclick="reopenTask(${t.id})"><i class="fas fa-rotate-left"></i> Reopen</button>
          ` : `
            <button class="control-btn ${t.active ? 'pause' : 'start'}" onclick="toggleTask(${t.id})">
              <i class="fas fa-${t.active ? 'pause' : 'play'}"></i> ${t.active ? 'Pause' : 'Start'}
            </button>
            <button class="control-btn" onclick="markDone(${t.id})"><i class="fas fa-check"></i> Done</button>
          `}
        </div>
      </div>`;
    }).join('');
  }
}

function escapeHtml(str) {
  const d = document.createElement('div');
  d.textContent = str;
  return d.innerHTML;
}

render();
