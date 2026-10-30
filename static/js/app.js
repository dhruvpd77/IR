(function () {
  function pad(n) {
    return String(n).padStart(2, '0');
  }

  function formatIdle(totalSeconds) {
    let seconds = Math.max(0, Math.floor(totalSeconds));
    const days = Math.floor(seconds / 86400);
    seconds %= 86400;
    const hours = Math.floor(seconds / 3600);
    seconds %= 3600;
    const minutes = Math.floor(seconds / 60);
    seconds %= 60;
    if (days > 0) return days + 'd ' + pad(hours) + 'h ' + pad(minutes) + 'm';
    return pad(hours) + 'h ' + pad(minutes) + 'm ' + pad(seconds) + 's';
  }

  function tickClocks() {
    const now = Date.now();
    document.querySelectorAll('[data-idle]').forEach(function (el) {
      const start = parseInt(el.dataset.start, 10) * 1000;
      if (!start) return;
      const end = el.dataset.end ? parseInt(el.dataset.end, 10) * 1000 : now;
      el.textContent = formatIdle((end - start) / 1000);
      if (!el.dataset.end && now - start >= 8 * 3600 * 1000) el.classList.add('clock-hot');
    });
    document.querySelectorAll('[data-clock]').forEach(function (clock) {
      const d = new Date();
      const stamp = d.toLocaleDateString('en-IN', { weekday: 'short', day: 'numeric', month: 'short' });
      clock.innerHTML = '<b>' + pad(d.getHours()) + ':' + pad(d.getMinutes()) + ':' + pad(d.getSeconds()) + '</b><span>' + stamp + '</span>';
    });
  }

  tickClocks();
  setInterval(tickClocks, 1000);

  const rejectDialog = document.getElementById('reject-dialog');
  const rejectForm = document.getElementById('reject-form');
  if (rejectDialog && rejectForm) {
    document.querySelectorAll('[data-reject]').forEach(function (button) {
      button.addEventListener('click', function () {
        rejectForm.action = button.dataset.reject;
        const note = rejectForm.querySelector('textarea');
        if (note) note.value = '';
        rejectDialog.showModal();
      });
    });
    rejectDialog.querySelectorAll('[data-reject-close]').forEach(function (button) {
      button.addEventListener('click', function () { rejectDialog.close(); });
    });
  }

  const pmDialog = document.getElementById('pm-complete-dialog');
  const pmForm = document.getElementById('pm-complete-form');
  if (pmDialog && pmForm) {
    document.querySelectorAll('[data-pm-complete]').forEach(function (button) {
      button.addEventListener('click', function () {
        pmForm.action = button.dataset.pmComplete;
        const title = document.getElementById('pm-complete-name');
        if (title) title.textContent = button.dataset.pmName || '';
        const date = pmForm.querySelector('input[type="date"]');
        if (date) date.value = button.dataset.pmToday || '';
        const note = pmForm.querySelector('textarea');
        if (note) {
          note.required = false;
          note.removeAttribute('required');
          note.removeAttribute('minlength');
          note.value = '';
        }
        pmDialog.showModal();
      });
    });
    pmDialog.querySelectorAll('[data-pm-close]').forEach(function (button) {
      button.addEventListener('click', function () { pmDialog.close(); });
    });
  }

  document.querySelectorAll('[data-file-name]').forEach(function (name) {
    const input = name.parentElement.querySelector('input[type="file"]');
    if (!input) return;
    input.addEventListener('change', function () {
      const file = input.files && input.files[0];
      name.textContent = file ? file.name : 'No file chosen';
    });
  });

  document.querySelectorAll('.toast').forEach(function (toast) {
    setTimeout(function () { toast.classList.add('is-out'); }, 4600);
  });

  document.querySelectorAll('[data-demo]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      const form = document.getElementById('login-form');
      const parts = btn.dataset.demo.split('|');
      form.username.value = parts[0];
      form.password.value = parts[1];
      form.submit();
    });
  });

  document.querySelectorAll('form.js-once').forEach(function (form) {
    form.addEventListener('submit', function () {
      const button = form.querySelector('[type="submit"]');
      if (button) {
        setTimeout(function () {
          button.disabled = true;
          button.textContent = 'Saving…';
        }, 0);
      }
    });
  });

  const toggle = document.getElementById('nav-toggle');
  const sidebar = document.querySelector('.sidebar');
  if (toggle && sidebar) {
    const backdrop = document.getElementById('nav-backdrop');
    function setNav(open) {
      sidebar.classList.toggle('is-open', open);
      document.body.classList.toggle('nav-open', open);
    }
    toggle.addEventListener('click', function () {
      setNav(!sidebar.classList.contains('is-open'));
    });
    if (backdrop) backdrop.addEventListener('click', function () { setNav(false); });
    sidebar.querySelectorAll('a').forEach(function (link) {
      link.addEventListener('click', function () { setNav(false); });
    });
  }

  const lightbox = document.getElementById('lightbox');
  if (lightbox) {
    document.querySelectorAll('[data-lightbox]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        lightbox.querySelector('img').src = btn.dataset.lightbox;
        lightbox.hidden = false;
      });
    });
    lightbox.addEventListener('click', function (event) {
      if (event.target === lightbox || event.target.closest('[data-lightbox-close]')) lightbox.hidden = true;
    });
    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape') lightbox.hidden = true;
    });
  }

  const wizard = document.getElementById('request-wizard');
  if (wizard) initWizard(wizard);
  const requestForm = document.getElementById('request-form');
  if (requestForm) initRequest(requestForm);

  const board = document.getElementById('board-root');
  if (board) initBoard(board);

  function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, function (ch) {
      return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[ch];
    });
  }

  function shake(el) {
    el.classList.remove('is-shake');
    void el.offsetWidth;
    el.classList.add('is-shake');
  }

  function bindFiles(input, list, zone) {
    function renderFiles() {
      if (!list || !input) return;
      list.innerHTML = '';
      Array.from(input.files).forEach(function (file) {
        const li = document.createElement('li');
        li.textContent = file.name + ' · ' + Math.max(1, Math.ceil(file.size / 1024)) + ' KB';
        list.appendChild(li);
      });
    }
    if (!input || !zone) return;
    zone.addEventListener('dragover', function (event) {
      event.preventDefault();
      zone.classList.add('is-hot');
    });
    zone.addEventListener('dragleave', function () { zone.classList.remove('is-hot'); });
    zone.addEventListener('drop', function (event) {
      event.preventDefault();
      zone.classList.remove('is-hot');
      const transfer = new DataTransfer();
      Array.from(event.dataTransfer.files).slice(0, 8).forEach(function (file) { transfer.items.add(file); });
      input.files = transfer.files;
      renderFiles();
    });
    input.addEventListener('change', renderFiles);
  }

  async function initRequest(form) {
    const stream = document.getElementById('field-category');
    const equipment = document.getElementById('field-subcategory');
    const location = document.getElementById('field-asset');
    const warn = document.getElementById('machine-warning');
    const chosenEquipment = form.dataset.selectedEquipment || '';
    const chosenLocation = form.dataset.selectedLocation || '';
    bindFiles(document.getElementById('media-input'), document.getElementById('file-list'), document.getElementById('dropzone'));

    function resetSelect(select, label, enabled) {
      select.innerHTML = '<option value="">' + label + '</option>';
      select.disabled = !enabled;
    }

    function fillSelect(select, rows, label, current, textOf) {
      resetSelect(select, label, rows.length > 0);
      rows.forEach(function (row) {
        const option = document.createElement('option');
        option.value = row.id;
        option.textContent = textOf(row);
        if (row.open) option.dataset.open = '1';
        if (String(row.id) === String(current)) option.selected = true;
        select.appendChild(option);
      });
    }

    async function loadEquipment(streamId, current) {
      resetSelect(equipment, 'Loading equipment…', false);
      resetSelect(location, 'Select the location', false);
      if (!streamId) {
        resetSelect(equipment, 'Select the equipment', false);
        return;
      }
      const response = await fetch(form.dataset.subUrl.replace('/0/', '/' + streamId + '/'));
      const data = await response.json();
      fillSelect(equipment, data.results, 'Select the equipment', current, function (row) { return row.name; });
    }

    async function loadLocations(equipmentId, current) {
      resetSelect(location, 'Loading locations…', false);
      if (warn) warn.classList.add('hidden');
      if (!equipmentId) {
        resetSelect(location, 'Select the location', false);
        return;
      }
      const response = await fetch(form.dataset.assetUrl.replace('/0/', '/' + equipmentId + '/'));
      const data = await response.json();
      fillSelect(location, data.results, 'Select the location', current, function (row) { return row.location; });
      showOpenWarning();
    }

    function showOpenWarning() {
      if (!warn) return;
      const option = location.options[location.selectedIndex];
      warn.classList.toggle('hidden', !(option && option.dataset.open === '1'));
    }

    stream.addEventListener('change', function () {
      loadEquipment(stream.value, '');
    });
    equipment.addEventListener('change', function () {
      loadLocations(equipment.value, '');
    });
    location.addEventListener('change', showOpenWarning);

    if (stream.value) {
      await loadEquipment(stream.value, chosenEquipment);
      if (equipment.value) await loadLocations(equipment.value, chosenLocation);
    }
  }

  async function initWizard(form) {
    let step = 1;
    const panels = Array.from(form.querySelectorAll('.step-panel'));
    const dots = Array.from(document.querySelectorAll('[data-step-dot]'));
    const back = document.getElementById('wiz-back');
    const next = document.getElementById('wiz-next');
    const submit = document.getElementById('wiz-submit');
    const catField = document.getElementById('field-category');
    const subField = document.getElementById('field-subcategory');
    const assetField = document.getElementById('field-asset');
    const names = {
      category: form.dataset.catName || '',
      subcategory: form.dataset.subName || '',
      asset: form.dataset.assetName || '',
    };

    function show(n) {
      step = n;
      panels.forEach(function (panel) {
        panel.classList.toggle('hidden', Number(panel.dataset.step) !== n);
      });
      dots.forEach(function (dot) {
        const index = Number(dot.dataset.stepDot);
        dot.classList.toggle('is-on', index === n);
        dot.classList.toggle('is-done', index < n);
      });
      back.classList.toggle('hidden', n === 1);
      next.classList.toggle('hidden', n === 4);
      submit.classList.toggle('hidden', n !== 4);
      if (n === 4) {
        const summary = document.getElementById('wiz-summary');
        summary.innerHTML =
          '<div><span>Category</span><b>' + escapeHtml(names.category || '—') + '</b></div>' +
          '<div><span>Fault</span><b>' + escapeHtml(names.subcategory || '—') + '</b></div>' +
          '<div><span>Machine</span><b>' + escapeHtml(names.asset || '—') + '</b></div>';
      }
    }

    document.querySelectorAll('[data-category]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        document.querySelectorAll('[data-category]').forEach(function (other) { other.classList.remove('is-selected'); });
        btn.classList.add('is-selected');
        catField.value = btn.dataset.category;
        names.category = btn.dataset.name;
        subField.value = '';
        assetField.value = '';
        names.subcategory = '';
        names.asset = '';
      });
    });

    if (catField.value) {
      const selected = form.querySelector('[data-category="' + catField.value + '"]');
      if (selected) selected.classList.add('is-selected');
    }

    async function loadSubs(id) {
      const grid = document.getElementById('sub-grid');
      grid.innerHTML = '<p class="muted">Loading fault types…</p>';
      const response = await fetch(form.dataset.subUrl.replace('/0/', '/' + id + '/'));
      const data = await response.json();
      grid.innerHTML = '';
      if (!data.results.length) {
        grid.innerHTML = '<p class="muted">No fault types in this category yet.</p>';
        return;
      }
      data.results.forEach(function (row) {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'choice-card';
        if (String(row.id) === String(subField.value)) btn.classList.add('is-selected');
        btn.innerHTML = '<span class="choice-title">' + escapeHtml(row.name) + '</span><span class="choice-copy">' + escapeHtml(row.description || '') + '</span>';
        btn.addEventListener('click', function () {
          grid.querySelectorAll('.choice-card').forEach(function (other) { other.classList.remove('is-selected'); });
          btn.classList.add('is-selected');
          subField.value = row.id;
          names.subcategory = row.name;
          assetField.value = '';
          names.asset = '';
        });
        grid.appendChild(btn);
      });
    }

    async function loadAssets(id) {
      const grid = document.getElementById('asset-grid');
      grid.innerHTML = '<p class="muted">Loading machines…</p>';
      const response = await fetch(form.dataset.assetUrl.replace('/0/', '/' + id + '/'));
      const data = await response.json();
      grid.innerHTML = '';
      if (!data.results.length) {
        grid.innerHTML = '<p class="muted">No machines are linked to this fault type yet.</p>';
        return;
      }
      data.results.forEach(function (row) {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'choice-card';
        if (String(row.id) === String(assetField.value)) btn.classList.add('is-selected');
        const state = row.open
          ? '<span class="pill status-pending"><span class="pill-dot"></span>Idle · ' + escapeHtml(row.open_ticket) + '</span>'
          : '<span class="pill status-completed">Running</span>';
        btn.innerHTML =
          '<span class="choice-code">' + escapeHtml(row.code) + '</span>' +
          '<span class="choice-title">' + escapeHtml(row.name) + '</span>' +
          '<span class="choice-copy">' + escapeHtml(row.location) + '</span>' + state;
        btn.addEventListener('click', function () {
          grid.querySelectorAll('.choice-card').forEach(function (other) { other.classList.remove('is-selected'); });
          btn.classList.add('is-selected');
          assetField.value = row.id;
          names.asset = row.code + ' · ' + row.name;
          const warn = document.getElementById('machine-warning');
          if (warn) warn.classList.toggle('hidden', !row.open);
        });
        grid.appendChild(btn);
      });
    }

    next.addEventListener('click', async function () {
      if (step === 1) {
        if (!catField.value) return shake(next);
        await loadSubs(catField.value);
        show(2);
      } else if (step === 2) {
        if (!subField.value) return shake(next);
        await loadAssets(subField.value);
        show(3);
      } else if (step === 3) {
        if (!assetField.value) return shake(next);
        show(4);
      }
    });

    back.addEventListener('click', async function () {
      const target = step - 1;
      if (target === 2 && catField.value && !document.querySelector('#sub-grid .choice-card')) await loadSubs(catField.value);
      if (target === 3 && subField.value && !document.querySelector('#asset-grid .choice-card')) await loadAssets(subField.value);
      show(target);
    });

    const input = document.getElementById('media-input');
    const list = document.getElementById('file-list');
    const zone = document.getElementById('dropzone');
    function renderFiles() {
      if (!list || !input) return;
      list.innerHTML = '';
      Array.from(input.files).forEach(function (file) {
        const li = document.createElement('li');
        li.textContent = file.name + ' · ' + Math.max(1, Math.ceil(file.size / 1024)) + ' KB';
        list.appendChild(li);
      });
    }
    if (input && zone) {
      zone.addEventListener('dragover', function (event) {
        event.preventDefault();
        zone.classList.add('is-hot');
      });
      zone.addEventListener('dragleave', function () { zone.classList.remove('is-hot'); });
      zone.addEventListener('drop', function (event) {
        event.preventDefault();
        zone.classList.remove('is-hot');
        const transfer = new DataTransfer();
        Array.from(event.dataTransfer.files).slice(0, 8).forEach(function (file) { transfer.items.add(file); });
        input.files = transfer.files;
        renderFiles();
      });
      input.addEventListener('change', renderFiles);
    }

    form.addEventListener('submit', function (event) {
      if (!catField.value || !subField.value || !assetField.value) {
        event.preventDefault();
        show(1);
        return;
      }
      setTimeout(function () {
        if (submit) {
          submit.disabled = true;
          submit.textContent = 'Submitting…';
        }
      }, 0);
    });

    const resumeStep = Number(form.dataset.resumeStep || 1);
    if (resumeStep >= 2 && catField.value) await loadSubs(catField.value);
    if (resumeStep >= 3 && subField.value) await loadAssets(subField.value);
    show(resumeStep);
  }

  function initBoard(root) {
    let status = new URLSearchParams(location.search).get('status') || 'open';
    const fs = document.getElementById('go-fullscreen');
    if (fs) {
      fs.addEventListener('click', function () {
        if (!document.fullscreenElement) document.documentElement.requestFullscreen();
        else document.exitFullscreen();
      });
    }
    document.querySelectorAll('[data-board-filter]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        status = btn.dataset.boardFilter;
        document.querySelectorAll('[data-board-filter]').forEach(function (other) {
          other.classList.toggle('is-on', other === btn);
        });
        refresh();
      });
    });
    const bar = document.querySelector('.refresh-bar span');
    let timer;
    function arm() {
      if (bar) {
        bar.style.animation = 'none';
        void bar.offsetWidth;
        bar.style.animation = '';
      }
      clearTimeout(timer);
      timer = setTimeout(refresh, 20000);
    }
    async function refresh() {
      try {
        const response = await fetch(location.pathname + '?partial=1&status=' + encodeURIComponent(status), {
          headers: { 'X-Requested-With': 'fetch' },
        });
        if (response.redirected) {
          location.href = response.url;
          return;
        }
        root.innerHTML = await response.text();
      } catch (err) {
        /* keep the board that is already on screen */
      }
      arm();
    }
    arm();
  }
})();
