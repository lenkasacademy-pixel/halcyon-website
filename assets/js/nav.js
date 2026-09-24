/* ==========================================================================
   The menu, for screens too narrow to carry the links in the bar.

   Below 1120px the primary links used to be display:none, which left a phone
   with no way into the site except the footer. They now fold into a panel
   behind a menu button.

   The button is built here rather than written into every page's markup:
   there is one copy of it, it cannot drift from the panel it controls, and if
   this script never runs there is no dead control left sitting in the bar.
   The links themselves are the ones already in the header, so their hrefs are
   whatever that page shipped — nothing to keep in step.

   Styling lives in the mobile-nav block that tools/build.py appends to each
   page's stylesheet.
   ========================================================================== */
(function () {
  'use strict';

  var root = document.documentElement;
  var header = document.querySelector('header.nav');
  var links = header && header.querySelector('.nav__links');
  if (!links) return;
  if (!links.id) links.id = 'navlinks';

  var burger = document.createElement('button');
  burger.type = 'button';
  burger.className = 'nav__burger';
  burger.setAttribute('aria-label', 'Menu');
  burger.setAttribute('aria-expanded', 'false');
  burger.setAttribute('aria-controls', links.id);
  burger.innerHTML = '<span></span><span></span><span></span>';
  header.appendChild(burger);

  function setOpen(open) {
    root.classList.toggle('nav-open', open);
    burger.setAttribute('aria-expanded', open ? 'true' : 'false');
  }

  burger.addEventListener('click', function () {
    setOpen(!root.classList.contains('nav-open'));
  });

  /* Any link closes it — including the in-page ones, which change nothing
     about the document and would otherwise leave the panel hanging open over
     the section they just jumped to. */
  links.addEventListener('click', function (e) {
    if (e.target.closest && e.target.closest('a')) setOpen(false);
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && root.classList.contains('nav-open')) {
      setOpen(false);
      burger.focus();
    }
  });

  /* turning the phone sideways can cross the breakpoint with it still open */
  window.addEventListener('resize', function () {
    if (window.innerWidth > 1120) setOpen(false);
  }, { passive: true });
})();
