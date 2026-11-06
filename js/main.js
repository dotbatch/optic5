(function () {
  // Mobile menu
  var toggle = document.querySelector('.menu-toggle');
  var links = document.getElementById('nav-links');
  if (toggle && links) {
    toggle.addEventListener('click', function () {
      var open = links.classList.toggle('open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    links.addEventListener('click', function (e) {
      if (e.target.tagName === 'A') {
        links.classList.remove('open');
        toggle.setAttribute('aria-expanded', 'false');
      }
    });
  }

  // Solid header once the page has scrolled
  var header = document.querySelector('.site-header');
  function onScroll() { header.classList.toggle('scrolled', window.scrollY > 40); }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  // Year
  var y = document.getElementById('year');
  if (y) y.textContent = new Date().getFullYear();

  // Reveal on scroll
  var items = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); }
      });
    }, { threshold: 0.12 });
    items.forEach(function (el) { io.observe(el); });
  } else {
    items.forEach(function (el) { el.classList.add('in'); });
  }

  // Busywork calculator
  var calc = document.getElementById('busywork-calc');
  if (calc) {
    var num = function (id) { return Math.max(0, parseFloat(document.getElementById(id).value) || 0); };
    var update = function () {
      var hours = num('c-people') * num('c-hours') * num('c-weeks');
      var saved = hours * Math.min(num('c-share'), 100) / 100;
      document.getElementById('c-out-hours').textContent = Math.round(hours).toLocaleString('en-US') + ' hrs';
      document.getElementById('c-out-cost').textContent = '$' + Math.round(hours * num('c-rate')).toLocaleString('en-US');
      document.getElementById('c-out-saved-hours').textContent = Math.round(saved).toLocaleString('en-US') + ' hrs';
      document.getElementById('c-out-saved').textContent = '$' + Math.round(saved * num('c-rate')).toLocaleString('en-US');
    };
    calc.addEventListener('input', update);
    update();
  }

  // Copy buttons
  document.querySelectorAll('[data-copy]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var text = document.getElementById(btn.getAttribute('data-copy')).innerText;
      navigator.clipboard.writeText(text).then(function () {
        btn.textContent = 'Copied';
      }, function () {
        btn.textContent = 'Select the text to copy it';
      });
    });
  });

  // Contact form (AJAX with graceful fallback to normal POST)
  var form = document.querySelector('.contact-form');
  if (!form) return;
  var status = form.querySelector('.form-status');
  form.addEventListener('submit', function (e) {
    var name = form.name.value.trim();
    var email = form.email.value.trim();
    var msg = form.message.value.trim();
    status.className = 'form-status';
    if (!name || !msg || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      e.preventDefault();
      status.textContent = 'Please add your name, a valid email, and a short message.';
      status.classList.add('err');
      return;
    }
    if (!window.fetch) return; // let the browser submit normally
    e.preventDefault();
    var btn = form.querySelector('button[type=submit]');
    btn.disabled = true;
    status.textContent = 'Sending…';
    fetch(form.action, {
      method: 'POST',
      body: new FormData(form),
      headers: { 'Accept': 'application/json' }
    })
      .then(function (r) { return r.json().catch(function () { return { ok: false }; }); })
      .then(function (data) {
        if (data.ok) {
          form.reset();
          status.textContent = "Thanks. We'll be in touch soon.";
          status.classList.add('ok');
        } else {
          throw new Error(data.error || 'send failed');
        }
      })
      .catch(function () {
        status.textContent = 'Something went wrong. Please email hello@optic5.com directly.';
        status.classList.add('err');
      })
      .finally(function () { btn.disabled = false; });
  });
})();
