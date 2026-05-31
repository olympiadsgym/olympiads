document.addEventListener('DOMContentLoaded', function () {

  const html = document.documentElement;
  const saved = localStorage.getItem('olympiads_theme') || '';
  html.setAttribute('data-theme', saved);

  function applyToggleIcon(btn, isDark) {
    if (!btn) return;
    const moon = btn.querySelector('.icon-moon');
    const sun  = btn.querySelector('.icon-sun');
    if (moon) moon.style.display = isDark ? 'none' : 'block';
    if (sun)  sun.style.display  = isDark ? 'block' : 'none';
  }

  function makeToggleHandler(btn) {
    if (!btn) return;
    applyToggleIcon(btn, saved === 'dark');
    btn.addEventListener('click', function () {
      const isDark = html.getAttribute('data-theme') === 'dark';
      const next = isDark ? '' : 'dark';
      html.setAttribute('data-theme', next);
      localStorage.setItem('olympiads_theme', next);
      document.querySelectorAll('.dark-toggle').forEach(function (b) {
        applyToggleIcon(b, next === 'dark');
      });
    });
  }

  document.querySelectorAll('.dark-toggle').forEach(function (btn) {
    makeToggleHandler(btn);
  });

  const menuBtn     = document.getElementById('menuBtn');
  const menuClose   = document.getElementById('menuClose');
  const menuOverlay = document.getElementById('menuOverlay');
  const menuDrawer  = document.getElementById('menuDrawer');

  function openMenu()  { if (menuDrawer) { menuDrawer.classList.add('open'); menuOverlay.classList.add('open'); document.body.style.overflow = 'hidden'; } }
  function closeMenu() { if (menuDrawer) { menuDrawer.classList.remove('open'); menuOverlay.classList.remove('open'); document.body.style.overflow = ''; } }

  if (menuBtn)     menuBtn.addEventListener('click', openMenu);
  if (menuClose)   menuClose.addEventListener('click', closeMenu);
  if (menuOverlay) menuOverlay.addEventListener('click', closeMenu);

  const planSelect    = document.getElementById('plan_id');
  const startInput    = document.getElementById('start_date');
  const expiryPreview = document.getElementById('expiry_preview');

  function updateExpiry() {
    if (!planSelect || !startInput || !expiryPreview) return;
    const selected = planSelect.options[planSelect.selectedIndex];
    const duration = parseInt(selected.getAttribute('data-duration'), 10);
    const startVal = startInput.value;
    if (!duration || !startVal) { expiryPreview.value = ''; return; }
    const start = new Date(startVal + 'T00:00:00');
    start.setDate(start.getDate() + duration);
    const y = start.getFullYear();
    const m = String(start.getMonth() + 1).padStart(2, '0');
    const d = String(start.getDate()).padStart(2, '0');
    expiryPreview.value = y + '-' + m + '-' + d;
  }

  if (planSelect) planSelect.addEventListener('change', updateExpiry);
  if (startInput) startInput.addEventListener('change', updateExpiry);
  updateExpiry();

  document.querySelectorAll('.flash').forEach(function (flash) {
    setTimeout(function () {
      flash.style.transition = 'opacity 0.4s';
      flash.style.opacity = '0';
      setTimeout(function () { flash.remove(); }, 400);
    }, 3500);
  });

  document.querySelectorAll('[data-confirm]').forEach(function (el) {
    el.addEventListener('click', function (e) {
      e.preventDefault();
      const message = el.getAttribute('data-confirm');
      showCustomConfirm(message, function () {
        // If confirmed, submit the form or click the element
        if (el.tagName === 'FORM') {
          el.submit();
        } else if (el.form) {
          el.form.submit();
        } else if (el.href) {
          window.location.href = el.href;
        }
      });
    });
  });

  // Custom confirmation modal
  function showCustomConfirm(message, onConfirm) {
    const overlay = document.getElementById('confirmModal');
    const titleEl = document.getElementById('modalTitle');
    const messageEl = document.getElementById('modalMessage');
    const confirmBtn = document.getElementById('modalConfirm');
    const cancelBtn = document.getElementById('modalCancel');

    if (!overlay) return; // Fallback if modal not found

    titleEl.textContent = 'Confirm Action';
    messageEl.textContent = message;

    overlay.classList.add('active');

    function cleanup() {
      overlay.classList.remove('active');
      confirmBtn.removeEventListener('click', handleConfirm);
      cancelBtn.removeEventListener('click', handleCancel);
      document.removeEventListener('keydown', handleEscape);
    }

    function handleConfirm() {
      cleanup();
      onConfirm();
    }

    function handleCancel() {
      cleanup();
    }

    function handleEscape(e) {
      if (e.key === 'Escape') {
        handleCancel();
      }
    }

    confirmBtn.addEventListener('click', handleConfirm);
    cancelBtn.addEventListener('click', handleCancel);
    document.addEventListener('keydown', handleEscape);
  }

  // Delegated/custom-dropdown handler — works for multiple instances and dynamic items
  document.addEventListener('click', function (e) {
    // Toggle dropdown when its button is clicked
    var btn = e.target.closest && e.target.closest('.custom-dropdown__btn');
    if (btn) {
      var wrapper = btn.closest('.custom-dropdown');
      var list = wrapper && wrapper.querySelector('.custom-dropdown__list');
      if (list) {
        e.stopPropagation();
        list.classList.toggle('open');
      }
      return;
    }

    // Handle clicks on dropdown items
    var item = e.target.closest && e.target.closest('.custom-dropdown__item');
    if (item) {
      var wrap = item.closest('.custom-dropdown');
      var listEl = wrap && wrap.querySelector('.custom-dropdown__list');
      var label = wrap && (wrap.querySelector('#statusDropdownLabel') || wrap.querySelector('.custom-dropdown__btn span'));
      var hidden = document.getElementById('statusHidden') || (wrap && wrap.closest('form') && wrap.closest('form').querySelector('input[type="hidden"][name="status"]'));
      if (label) label.textContent = item.textContent;
      if (hidden) hidden.value = item.getAttribute('data-value') || '';
      wrap.querySelectorAll('.custom-dropdown__item').forEach(function (i) { i.classList.remove('custom-dropdown__item--active'); });
      item.classList.add('custom-dropdown__item--active');
      if (listEl) listEl.classList.remove('open');
      var form = wrap && wrap.closest('form');
      if (form) form.submit();
      return;
    }

    // Click outside: close any open dropdown lists
    document.querySelectorAll('.custom-dropdown__list.open').forEach(function (l) { l.classList.remove('open'); });
  });

  // EH-11: network error detection for all POST form submissions.
  // A network failure (offline, timeout, DNS failure) is distinct from a
  // server-side validation error — the server never receives the request so
  // no Django error page is returned. We detect it via fetch and show an
  // inline banner so the user knows the action did not go through.
  document.querySelectorAll('form[method="post"]').forEach(function (form) {
    form.addEventListener('submit', function (e) {
      // Skip forms that opt out (e.g. file uploads with enctype)
      if (form.dataset.noNetworkCheck) return;

      // Only intercept if we can reasonably use fetch (modern browsers)
      if (typeof fetch === 'undefined') return;

      e.preventDefault();

      var submitBtn = form.querySelector('[type="submit"]');
      var originalText = submitBtn ? submitBtn.textContent : null;
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = 'Submitting…';
      }

      // Remove any previous network-error banner on this form
      var prev = form.querySelector('.network-error-banner');
      if (prev) prev.remove();

      var formData = new FormData(form);
      var action = form.action || window.location.href;

      fetch(action, {
        method: 'POST',
        body: formData,
        credentials: 'same-origin',
        // No redirect: 'manual' — we want the browser to follow redirects normally
      })
      .then(function (response) {
        // Server responded (even with 4xx/5xx) — let the browser handle it
        // by navigating to the response URL (handles both redirects and re-renders)
        return response.text().then(function (html) {
          if (response.redirected || response.url !== window.location.href) {
            window.location.href = response.url;
          } else {
            // Server returned a page in-place (e.g. validation errors) — replace DOM
            document.open();
            document.write(html);
            document.close();
          }
        });
      })
      .catch(function () {
        // Network failure — server was never reached; no data was committed
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.textContent = originalText;
        }
        var banner = document.createElement('div');
        banner.className = 'flash flash--error network-error-banner';
        banner.setAttribute('role', 'alert');
        banner.textContent =
          'The action could not be completed — please check your connection and try again. ' +
          'No data was saved.';
        form.insertAdjacentElement('beforebegin', banner);
        banner.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      });
    });
  });

  // Midnight auto-logout: check every minute if it's past midnight
  function checkMidnight() {
    var now = new Date();
    if (now.getHours() === 0 && now.getMinutes() === 0) {
      // Redirect to logout at midnight
      var logoutLink = document.querySelector('a[href*="logout"]');
      window.location.href = logoutLink ? logoutLink.href : '/';
    }
  }
  setInterval(checkMidnight, 60000); // Check every minute

});

// Password visibility toggle — used on login & change-password pages
function togglePw(inputId, btn) {
  var input = document.getElementById(inputId);
  if (!input || !btn) return;
  var show = input.type === 'password';
  input.type = show ? 'text' : 'password';
  var eyeOn  = btn.querySelector('.eye-icon');
  var eyeOff = btn.querySelector('.eye-off-icon');
  if (eyeOn)  eyeOn.style.display  = show ? 'none' : '';
  if (eyeOff) eyeOff.style.display = show ? ''     : 'none';
}