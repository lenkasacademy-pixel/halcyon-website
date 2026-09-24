/* ==========================================================================
   Cookie consent, and Google Tag Manager behind it.

   Nothing that tracks anyone loads until the visitor says yes: Tag Manager is
   injected only after "Accept", so a visitor who ignores or declines the notice
   leaves no cookies behind. The choice is remembered in this browser for a year
   and can be changed from the privacy policy (a link with data-consent="reset").

   The container id is set by tools/build.py from SITE['gtm_id'].
   ========================================================================== */
(function () {
  'use strict';

  var me = document.currentScript;
  var GTM = (me && me.getAttribute('data-gtm')) || '';
  var ROOT = new URL((me && me.getAttribute('data-root')) || './', location.href).href;
  var KEY = 'halcyon.consent';
  var YEAR = 365 * 864e5;

  function get() {
    try {
      var v = JSON.parse(localStorage.getItem(KEY) || 'null');
      if (v && Date.now() - v.at < YEAR) return v.ok ? 'yes' : 'no';
    } catch (e) {}
    return '';
  }
  function set(ok) {
    try { localStorage.setItem(KEY, JSON.stringify({ ok: ok, at: Date.now() })); } catch (e) {}
  }

  var loaded = false;
  function loadGTM() {
    if (loaded || !GTM) return;
    loaded = true;
    window.dataLayer = window.dataLayer || [];
    window.dataLayer.push({ 'gtm.start': new Date().getTime(), event: 'gtm.js' });
    var s = document.createElement('script');
    s.async = true;
    s.src = 'https://www.googletagmanager.com/gtm.js?id=' + encodeURIComponent(GTM);
    document.head.appendChild(s);
  }

  function banner() {
    var box = document.createElement('div');
    box.className = 'ck';
    box.setAttribute('role', 'dialog');
    box.setAttribute('aria-label', 'Cookies');
    box.innerHTML =
      '<p>We would like to use cookies to see how this site is used, so we can improve it. ' +
      'Nothing is set unless you agree. <a href="' + ROOT + 'privacy-policy/">Privacy policy</a></p>' +
      '<div class="ck__row"><button type="button" class="ck__yes">Accept</button>' +
      '<button type="button" class="ck__no">Decline</button></div>';
    document.body.appendChild(box);
    requestAnimationFrame(function () { box.classList.add('is-on'); });
    box.querySelector('.ck__yes').addEventListener('click', function () { set(true); loadGTM(); close(box); });
    box.querySelector('.ck__no').addEventListener('click', function () { set(false); close(box); });
  }
  function close(box) {
    box.classList.remove('is-on');
    setTimeout(function () { box.remove(); }, 400);
  }

  var choice = get();
  if (choice === 'yes') loadGTM();
  else if (choice !== 'no') {
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', banner);
    else banner();
  }

  /* "Change cookie choice" anywhere on the site */
  document.addEventListener('click', function (e) {
    var t = e.target.closest && e.target.closest('[data-consent="reset"]');
    if (!t) return;
    e.preventDefault();
    try { localStorage.removeItem(KEY); } catch (err) {}
    if (!document.querySelector('.ck')) banner();
  });
})();
