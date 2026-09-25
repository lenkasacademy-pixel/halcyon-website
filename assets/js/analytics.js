/* ==========================================================================
   Google Tag Manager.

   Loaded on every page view. There is no cookie banner: the clinic decided
   the notice was not worth the interruption, and measuring only the visitors
   who pressed "Accept" was undercounting badly enough to make the numbers
   misleading.

   The one exception is a visitor whose browser is already asking not to be
   tracked — Do Not Track or Global Privacy Control. Neither is binding on a
   clinic in India, but someone who has gone and set it has said what they
   want, and skipping the tag for them costs nothing.

   What this does is written plainly in the privacy policy under "Cookies and
   measurement", including how to opt out. If this file changes, that section
   changes with it. A privacy policy that does not match the code is worse
   than no privacy policy at all.

   The container id comes from SITE['gtm_id'] in tools/build.py.
   ========================================================================== */
(function () {
  'use strict';

  var me = document.currentScript;
  var GTM = (me && me.getAttribute('data-gtm')) || '';
  if (!GTM) return;

  /* asked not to be tracked — load nothing at all */
  if (navigator.doNotTrack === '1' || window.doNotTrack === '1' ||
      navigator.globalPrivacyControl === true) return;

  window.dataLayer = window.dataLayer || [];
  window.dataLayer.push({ 'gtm.start': new Date().getTime(), event: 'gtm.js' });

  var s = document.createElement('script');
  s.async = true;
  s.src = 'https://www.googletagmanager.com/gtm.js?id=' + encodeURIComponent(GTM);
  document.head.appendChild(s);
})();
