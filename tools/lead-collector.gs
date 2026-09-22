/**
 * Halcyon — website lead collector (Google Apps Script)
 *
 * Receives call-back requests from the website assistant and writes each one
 * as a row in this Google Sheet, then emails the clinic.
 *
 * ONE-TIME SETUP (about five minutes, from the clinic's Google account):
 *   1. Create a new Google Sheet, e.g. "Halcyon — Website leads".
 *   2. Extensions → Apps Script. Delete what is there, paste this whole file, Save.
 *   3. Set NOTIFY_EMAIL below (leave '' to email the account that owns the Sheet).
 *   4. In the toolbar choose the function `setup` and press Run. Approve the
 *      permissions it asks for (it needs this Sheet, and Gmail to send the alert).
 *   5. Deploy → New deployment → type "Web app".
 *        Execute as: Me    ·    Who has access: Anyone
 *      Deploy, then copy the Web app URL (it ends in /exec).
 *   6. Put that URL in tools/build.py (SITE['lead_endpoint']) and run
 *      python3 tools/build.py — or send it to whoever maintains the site.
 *
 * After editing this script later, use Deploy → Manage deployments → Edit →
 * Version: New version, so the same URL keeps working.
 *
 * What it stores: name, mobile, what hurts, for how long, scans done, best time
 * to call, the questions asked in the chat, the page and ad (UTM / gclid /
 * fbclid) the visitor came from, and when they consented. Nothing else.
 */

var NOTIFY_EMAIL = '';            // e.g. 'info@halcyonpainfree.com' — '' = the Sheet owner
var SHEET = 'Leads';
var DUPLICATE_MINUTES = 30;       // same mobile within this window = the same request

var COLUMNS = [
  ['Received',        function (p) { return new Date(); }],
  ['Status',          function (p) { return 'New'; }],
  ['Name',            function (p) { return p.name; }],
  ['Mobile',          function (p) { return p.phone; }],
  ['Pain',            function (p) { return p.area; }],
  ['For how long',    function (p) { return p.since; }],
  ['Scans',           function (p) { return p.scans; }],
  ['Best time',       function (p) { return p.callback_time; }],
  ['Questions asked', function (p) { return p.questions; }],
  ['Page',            function (p) { return p.page; }],
  ['Landing page',    function (p) { return p.landing; }],
  ['Source',          function (p) { return p.utm_source || (p.gclid || p.gbraid || p.wbraid ? 'google-ads' : p.fbclid ? 'facebook' : refHost(p.referrer) || 'direct'); }],
  ['Medium',          function (p) { return p.utm_medium; }],
  ['Campaign',        function (p) { return p.utm_campaign; }],
  ['Ad / content',    function (p) { return p.utm_content; }],
  ['Keyword',         function (p) { return p.utm_term; }],
  ['Referrer',        function (p) { return p.referrer; }],
  ['First visit',     function (p) { return p.first_touch; }],
  ['Click id',        function (p) { return p.gclid || p.gbraid || p.wbraid || p.fbclid || p.msclkid; }],
  ['Device',          function (p) { return p.device; }],
  ['Topics',          function (p) { return p.topics; }],
  ['Consent',         function (p) { return p.consent; }],
  ['Lead id',         function (p) { return p.id; }],
  ['Notes',           function (p) { return ''; }]
];
var STATUSES = ['New', 'Called — no answer', 'Called — follow up', 'Booked', 'Visited', 'Not interested', 'Duplicate / spam'];

function doPost(e) {
  var lock = LockService.getScriptLock();
  try {
    lock.waitLock(10000);
    var p = JSON.parse((e && e.postData && e.postData.contents) || '{}');
    if (p.hp) return reply({ ok: true });                       // honeypot: pretend, store nothing
    var mobile = String(p.phone || '').replace(/\D/g, '').slice(-10);
    if (!/^[6-9]\d{9}$/.test(mobile)) return reply({ ok: false, error: 'invalid mobile' });
    if (String(p.consent || '').indexOf('yes') !== 0) return reply({ ok: false, error: 'no consent' });

    var cache = CacheService.getScriptCache();
    if (p.id && cache.get('id:' + p.id)) return reply({ ok: true, duplicate: true });
    var dupe = cache.get('m:' + mobile);

    var sh = sheet();
    var row = COLUMNS.map(function (c) { return clean(c[1](p)); });
    row[0] = new Date();
    if (dupe) row[1] = 'Duplicate / spam';
    sh.appendRow(row);

    if (p.id) cache.put('id:' + p.id, '1', 21600);
    cache.put('m:' + mobile, '1', DUPLICATE_MINUTES * 60);
    if (!dupe) notify(p, row);
    return reply({ ok: true });
  } catch (err) {
    return reply({ ok: false, error: String(err) });
  } finally {
    try { lock.releaseLock(); } catch (x) {}
  }
}

function doGet() { return reply({ ok: true, service: 'halcyon-leads' }); }

/* ---------------------------------------------------------------- setup */
function setup() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sh = ss.getSheetByName(SHEET) || ss.insertSheet(SHEET, 0);
  sh.getRange(1, 1, 1, COLUMNS.length).setValues([COLUMNS.map(function (c) { return c[0]; })])
    .setFontWeight('bold').setBackground('#2C0A1B').setFontColor('#FBF8F9');
  sh.setFrozenRows(1);
  sh.getRange('A:A').setNumberFormat('dd mmm yyyy, hh:mm');
  sh.getRange('D:D').setNumberFormat('@');
  var rule = SpreadsheetApp.newDataValidation().requireValueInList(STATUSES, true).setAllowInvalid(false).build();
  sh.getRange(2, 2, sh.getMaxRows() - 1, 1).setDataValidation(rule);
  sh.setColumnWidths(1, COLUMNS.length, 140);
  sh.setColumnWidth(9, 320);

  // which source / campaign brings leads, and which of them book
  var dash = ss.getSheetByName('By source') || ss.insertSheet('By source');
  dash.clear();
  var L = "'" + SHEET + "'!";
  dash.getRange('A1').setValue('Leads by source and campaign').setFontWeight('bold');
  dash.getRange('A2').setFormula(
    '=IFERROR(QUERY({' + L + 'L2:L, ' + L + 'N2:N, ' + L + 'B2:B}, ' +
    '"select Col1, Col2, count(Col1) where Col1 is not null group by Col1, Col2 label Col1 \'Source\', Col2 \'Campaign\', count(Col1) \'Leads\'", 0), "No leads yet")');
  dash.getRange('F1').setValue('Booked or visited, by campaign').setFontWeight('bold');
  dash.getRange('F2').setFormula(
    '=IFERROR(QUERY({' + L + 'L2:L, ' + L + 'N2:N, ' + L + 'B2:B}, ' +
    '"select Col1, Col2, count(Col1) where Col3 = \'Booked\' or Col3 = \'Visited\' group by Col1, Col2 label Col1 \'Source\', Col2 \'Campaign\', count(Col1) \'Booked\'", 0), "None yet")');
  dash.getRange('K1').setValue('Leads by week').setFontWeight('bold');
  dash.getRange('K2').setFormula(
    '=IFERROR(QUERY({ARRAYFORMULA(IF(' + L + 'A2:A="",,TEXT(' + L + 'A2:A-WEEKDAY(' + L + 'A2:A,3),"yyyy-mm-dd"))), ' + L + 'C2:C}, ' +
    '"select Col1, count(Col2) where Col2 is not null group by Col1 order by Col1 desc label Col1 \'Week from\', count(Col2) \'Leads\'", 0), "")');
  dash.getRange('P1').setValue('What people ask about').setFontWeight('bold');
  dash.getRange('P2').setFormula(
    '=IFERROR(QUERY({' + L + 'E2:E}, "select Col1, count(Col1) where Col1 is not null group by Col1 order by count(Col1) desc label Col1 \'Pain\', count(Col1) \'Leads\'", 0), "")');
  SpreadsheetApp.flush();
}

/* ---------------------------------------------------------------- helpers */
function sheet() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sh = ss.getSheetByName(SHEET);
  if (!sh) { setup(); sh = ss.getSheetByName(SHEET); }
  return sh;
}

function notify(p, row) {
  var to = NOTIFY_EMAIL || Session.getEffectiveUser().getEmail();
  if (!to) return;
  var mobile = String(p.phone || '');
  var subject = 'New website lead: ' + (p.name || 'No name') + ' — ' + (p.area || 'enquiry') + ' — ' + mobile;
  var lines = COLUMNS.map(function (c, i) { return c[0] + ': ' + (row[i] instanceof Date ? row[i].toString() : row[i]); })
                     .filter(function (l) { return !/: $/.test(l); });
  var body = 'A call-back request came in from the website assistant.\n\n' + lines.join('\n') +
             '\n\nCall: tel:' + mobile.replace(/\s/g, '') +
             '\nWhatsApp: https://wa.me/91' + mobile.replace(/\D/g, '').slice(-10) +
             '\nSheet: ' + SpreadsheetApp.getActiveSpreadsheet().getUrl();
  try { MailApp.sendEmail({ to: to, subject: subject, body: body }); } catch (err) {}
}

function clean(v) {
  if (v === null || v === undefined) return '';
  if (v instanceof Date) return v;
  var s = String(v).slice(0, 1000);
  return /^[=+\-@]/.test(s) ? "'" + s : s;       // never let a lead inject a formula
}

function refHost(r) {
  var m = String(r || '').match(/^https?:\/\/([^\/]+)/);
  return m ? m[1].replace(/^www\./, '') : '';
}

function reply(o) {
  return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON);
}
