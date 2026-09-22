# Halcyon Pain Management Centre — website

Static prototype for Halcyon Pain Management Centre, Kukatpally, Hyderabad. Six linked
pages, each a single self-contained HTML file: fonts, images and scripts are inlined, so
any page opens on its own with no build step, no dependencies and no network calls.

## Pages

| File | What it is |
| --- | --- |
| `index.html` | Home. Hero, the four treatment pathways, the conditions conveyor, the interactive body map, the visit timeline, patient stories, and the assistant. |
| `Halcyon-Treatments.html` | The four interventional pathways in full, the named procedures they are delivered as, and what none of them involve. |
| `Halcyon-Conditions.html` | All twelve pain conditions, filterable by part of the body, with the usual procedure for each. |
| `Halcyon-Consultants.html` | Dr. Dasyam Pallavi and Dr. PSS Kiran — qualifications, background and what they treat. |
| `Halcyon-About.html` | The clinic: how it works, the numbers, the people, and where it is. |
| `Halcyon-Privacy.html` | Privacy policy. **Draft — see below.** |

Every page links to every other. Conditions and treatments cross-link by anchor
(`Halcyon-Conditions.html#knee-pain`, `Halcyon-Treatments.html#prolotherapy`), and the
footer's condition and treatment lists resolve to those anchors.

## Also in here

- `Halcyon-YourVisit-demo.html` — an earlier standalone demo of the visit timeline, kept
  for reference. Superseded by the `#jr` section on the home page and linked from nowhere.
- `shoulder-pain.html` — an older, separate shoulder-pain landing page in a different
  design. Not part of the six-page site and not linked from it.

## Before this goes live

1. **The privacy policy is a working draft.** It carries a visible "not yet reviewed"
   notice and ten highlighted placeholders marking decisions only the clinic can make —
   retention periods, which providers hold patient data, the grievance officer, and so on.
   It is written against India's Digital Personal Data Protection Act, 2023 but is not
   legal advice and needs a lawyer's review. Delete the notice box once it has one.
2. **Consultant biography prose needs confirming.** Qualifications, certifications and
   fellowships come from the clinic's own copy, but the connective narrative on the
   consultants page is inference and should be checked by the doctors.
3. **Two footer links have no page yet** — the social icons point nowhere, since the
   clinic's profile URLs were not available.

## Contact routes wired into the site

All booking buttons, the assistant's call button and its WhatsApp hand-off reach
**+91 77880 91092**. Contact listings that print **+91 95536 04226** dial that number, so
no link disagrees with the number beside it.
