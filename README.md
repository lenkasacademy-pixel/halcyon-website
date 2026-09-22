# Halcyon Pain Management Centre — website

Static site for Halcyon Pain Management Centre, Kukatpally, Hyderabad. It is built to
replace the WordPress site at **https://halcyonpainfree.com/**, and every page keeps the
address the old site ranked with, so existing Google rankings carry over.

Preview (until the domain moves): https://lenkasacademy-pixel.github.io/halcyon-website/

## Pages

| Address | What it is | Made by |
| --- | --- | --- |
| `/` | Home — hero, treatment pathways, conditions, body map, doctors, visit timeline, patient stories, FAQ, assistant | hand |
| `/services/` | The four treatment pathways, linking to each treatment page | hand |
| `/pain-conditions/` | All twelve conditions, filterable, linking to each condition page | hand |
| `/our-doctors/` | Both consultants, linking to each profile | hand |
| `/about-us/` | The clinic | hand |
| `/privacy-policy/` | Privacy policy — **draft, see below** | hand |
| `/contact/` | Address, hours, phone, directions, FAQ | `tools/build.py` |
| `/knee-pain-treatment/` … (12) | One page per condition | `tools/build.py` from `tools/content/conditions/*.json` |
| `/regenerative-medicine/` … (4) | One page per treatment | `tools/build.py` from `tools/content/treatments/*.json` |
| `/dr-d-pallavi-profile/`, `/dr-pss-kiran-profile/` | Doctor profiles | `tools/build.py` from `tools/content/doctors/*.json` |

Old addresses redirect to their new equivalent: the flat `Halcyon-*.html` files this
prototype used to publish, `shoulder-pain.html`, and the old WordPress pages that have no
page of the same name (`/book-an-appointment/`, `/our-practice/`, the four blog posts, the
ad landing pages …). Each is a tiny page with an instant redirect, `noindex` and a
canonical pointing at the new address. `Halcyon-YourVisit-demo.html` is an old demo, kept
but `noindex`.

Images and fonts live in `assets/` (images are WebP with descriptive file names). Pages
link with relative paths, so the site works both at the domain root and on the preview
URL. To look at it locally, serve the folder rather than opening files directly:
`python3 -m http.server` then http://localhost:8000/.

## The search layer — `tools/build.py`

Run `python3 tools/build.py` after changing anything in `tools/content/` or the facts at
the top of `tools/build.py`; then `python3 tools/check.py`, which must report 0 errors
before publishing. The build is safe to re-run. It:

- renders the 19 generated pages in the site's own design (header, footer, hero, CTA and
  scripts are lifted from `services/index.html`, so they never drift from it);
- rewrites the block between `<!-- seo:start -->` and `<!-- seo:end -->` in every page's
  `<head>`: title, description, canonical, robots, hreflang, Open Graph and Twitter cards,
  geo tags, icons, font preloads, and a JSON-LD graph (MedicalClinic, WebSite, page type,
  BreadcrumbList, MedicalCondition / TherapeuticProcedure / Person, FAQPage). **Edit the
  build, not the block** — hand edits inside it are overwritten;
- keeps the hand-made pages' extras in place: the hub cards' links to topic pages, the
  home page FAQ (between `<!-- faq:start -->` / `<!-- faq:end -->`), the first patient
  story rendered into the HTML, image dimensions and alt text;
- writes `sitemap.xml` (with images), `robots.txt` (every search engine and AI crawler
  allowed, by name), `llms.txt` and `llms-full.txt` (the site in plain text for AI
  assistants), `site.webmanifest` and `404.html`;
- generates the 1200×630 share images in `assets/og/` when they are missing (delete one
  to regenerate it). This step needs `pip install -r tools/requirements.txt`.

The clinic's name, address, phone and hours are defined once, in `SITE` at the top of
`tools/build.py`. The phone number must stay identical to the Google Business Profile
(+91 77880 91092).

## Launch checklist

1. **Point the domain here.** Add a `CNAME` file containing `halcyonpainfree.com`, set the
   custom domain in the repo's GitHub Pages settings, and change the DNS records at the
   registrar to GitHub Pages. Do this only when ready to switch — the moment `CNAME`
   exists, the preview URL starts redirecting to the domain. `robots.txt` and
   `sitemap.xml` only take effect once the site is at the domain root.
2. **Google Search Console:** verify halcyonpainfree.com (DNS record), submit
   `https://halcyonpainfree.com/sitemap.xml`, and use URL Inspection → Request indexing on
   the home page and the 12 condition pages. Watch Pages → "Not found (404)" for a few
   weeks for any old URL that still needs a redirect.
3. **Bing Webmaster Tools:** import from Search Console and submit the sitemap. Bing's
   index also feeds ChatGPT search and Copilot.
4. **Google Business Profile:** set the website to `https://halcyonpainfree.com/` and the
   appointment link to `https://halcyonpainfree.com/contact/`; keep name, address, phone
   and hours identical to the site.
5. **Test:** paste a few URLs into https://search.google.com/test/rich-results and
   https://validator.schema.org/.
6. **Ads:** the old `/pain-relief-ad1/` and `/pain-relief-ad2/` landing pages now redirect
   to the home page. Point live ad campaigns at a condition page instead.

## Before this goes live

1. **Medical copy needs the doctors' review.** The 18 topic pages were written from the
   clinic's own copy, but they add standard explanations and a few specific statements
   that should be confirmed:
   - knee radiofrequency is described as following a diagnostic block of the genicular nerves;
   - prolotherapy as "most commonly a concentrated dextrose solution";
   - hydrodissection fluid as "usually saline, sometimes with local anaesthetic or dextrose";
     nerve blocks as "usually a local anaesthetic and sometimes a steroid";
   - trigeminal neuralgia RF as "image-guided" and repeatable, with numbness as a possible effect;
   - hip is linked only to regenerative medicine; shoulder and sciatica/slipped disc to the
     nerve-blocks page (suprascapular block, epidural / transforaminal injection);
   - the doctors' profiles describe their approach from the site's own copy — no years of
     experience, past hospitals or colleges are stated.
   Once reviewed, a visible "Medically reviewed by …" line and `reviewedBy` /
   `lastReviewed` in the schema are worth adding — they are strong trust signals for
   health pages. They are deliberately absent until a review has happened.
2. **The privacy policy is a working draft.** It carries a visible "not yet reviewed"
   notice and highlighted placeholders for decisions only the clinic can make. It is
   written against India's Digital Personal Data Protection Act, 2023 but is not legal
   advice and needs a lawyer's review.
3. **Social profiles.** `sameAs` in the schema lists the Facebook, Instagram, LinkedIn,
   YouTube and X accounts linked from the old site. The old site linked two accounts on
   some networks; keep only the ones the clinic still runs. The footer's social icons
   still point nowhere.

## Contact routes wired into the site

All booking buttons, the assistant's call button and its WhatsApp hand-off reach
**+91 77880 91092**. Contact listings that print **+91 95536 04226** dial that number, so
no link disagrees with the number beside it.
