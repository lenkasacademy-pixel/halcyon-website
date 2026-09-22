#!/usr/bin/env python3
"""Build the search layer of the Halcyon site.

    python3 tools/build.py            # from the repo root

What it does, every run (it is safe to re-run):
  * renders one page per condition, treatment and doctor from tools/content/**.json,
    plus the contact page, in the site's own design (header, footer, hero, CTA and
    scripts are lifted from services/index.html so the pages never drift from it);
  * rewrites the SEO block of every page's <head> — title, description, canonical,
    Open Graph, geo tags, icons, font preloads and a JSON-LD graph — between
    <!-- seo:start --> and <!-- seo:end -->;
  * keeps the hand-made pages' crawlable extras in place (links from the hub cards to
    the topic pages, the home page FAQ, image dimensions);
  * writes sitemap.xml, robots.txt, llms.txt, llms-full.txt, site.webmanifest, 404.html.

Needs Pillow, fontTools and brotli only for the Open Graph images (tools/requirements.txt);
they are generated once and skipped when present.
"""
import datetime, glob, html, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
TODAY = datetime.date.today().isoformat()

# ============================================================================ facts
# Confirmed with the clinic. The phone number must match the Google Business Profile.
SITE = {
    'url': 'https://halcyonpainfree.com/',
    'name': 'Halcyon Pain Management Centre',
    'alt_names': ['Halcyon', 'Halcyon Pain Clinic', 'Halcyon Pain Management Center'],
    'tel': '+917788091092', 'tel_display': '+91 77880 91092', 'tel_schema': '+91-77880-91092',
    'tel2': '+919553604226', 'tel2_display': '+91 95536 04226',
    'wa': '917788091092',
    'email': 'info@halcyonpainfree.com',
    'street': '3rd Floor, KKR Commercial Complex, Kukatpally Y Junction, Moosapet Road',
    'area': 'Kukatpally', 'city': 'Hyderabad', 'region': 'Telangana', 'region_code': 'IN-TG',
    'postal': '500072', 'country': 'IN',
    'lat': 17.4753729, 'lng': 78.4230858,  # the Google Business Profile pin
    'map': 'https://maps.google.com/?cid=14254788734567695869',
    'landmark': 'Above the Max showroom at Kukatpally Y Junction, on Moosapet Road — a few minutes from the KPHB and Moosapet metro stations.',
    'hours': [('Monday', 'Saturday', '09:00', '18:00')],
    'hours_text': 'Monday to Saturday, 9 am – 6 pm. Closed on Sunday.',
    'description': ('Halcyon Pain Management Centre in Kukatpally, Hyderabad treats knee, back, neck, '
                    'shoulder, nerve and sports pain without surgery. The consultant who examines you '
                    'scans you with diagnostic ultrasound and, when a procedure is right, performs it in '
                    'the same appointment — image-guided, under local anaesthetic, as day care.'),
    'same_as': [
        'https://www.facebook.com/Halcyonpainmanagement/',
        'https://www.instagram.com/halcyonpainmanagementcenter/',
        'https://www.linkedin.com/company/halcyon-pain-management-center/',
        'https://www.youtube.com/channel/UCixQIloKFhlLDODkwtKoccg',
        'https://twitter.com/HalcyonPain',
    ],
    'area_served': ['Hyderabad', 'Kukatpally', 'KPHB Colony', 'Moosapet', 'Balanagar', 'Miyapur',
                    'Nizampet', 'Bachupally', 'Kondapur', 'Madhapur', 'HITEC City', 'Secunderabad'],
}
U = SITE['url']
ORG = U + '#organization'
WEBSITE = U + '#website'

AI_BOTS = [  # named so nobody later mistakes silence for a block
    'GPTBot', 'OAI-SearchBot', 'ChatGPT-User', 'ClaudeBot', 'Claude-SearchBot', 'Claude-User',
    'anthropic-ai', 'PerplexityBot', 'Perplexity-User', 'Google-Extended', 'GoogleOther',
    'Googlebot', 'Googlebot-Image', 'Bingbot', 'Applebot', 'Applebot-Extended', 'DuckDuckBot',
    'DuckAssistBot', 'CCBot', 'meta-externalagent', 'FacebookBot', 'Amazonbot', 'cohere-ai',
    'MistralAI-User', 'YouBot', 'Bytespider', 'PetalBot', 'YandexBot',
]

# ============================================================================ content
def load(kind):
    out = {}
    for f in sorted(glob.glob('tools/content/%s/*.json' % kind)):
        d = json.load(open(f))
        out[d['slug']] = d
    return out

CONDITIONS = load('conditions')
TREATMENTS = load('treatments')
DOCTORS = load('doctors')

# display order on hubs and in llms.txt — the order the site already uses
COND_ORDER = ['knee-pain-treatment', 'low-back-pain-treatment', 'neck-pain-treatment', 'shoulder-pain',
              'sciatica', 'slipped-disc-treatment', 'the-best-hip-pain-treatment-in-hyderabad',
              'sports-injuries-treatment', 'trigeminal-neuralgia-treatment',
              'advanced-elbow-hand-and-wrist-pain-treatment', 'foot-ankle-pain-treatment',
              'cervical-spondylosis-treatment']
TREAT_ORDER = ['regenerative-medicine', 'radiofrequency-ablations', 'prolotherapy',
               'non-surgical-nerve-hydrodissection-nerve-blocks']
DOC_ORDER = ['dr-d-pallavi-profile', 'dr-pss-kiran-profile']

# anchor ids the hub pages already use -> topic page slugs
COND_ANCHOR = {'knee-pain': 'knee-pain-treatment', 'low-back-pain': 'low-back-pain-treatment',
               'neck-pain': 'neck-pain-treatment', 'shoulder-pain': 'shoulder-pain', 'sciatica': 'sciatica',
               'slipped-disc': 'slipped-disc-treatment', 'hip-pain': 'the-best-hip-pain-treatment-in-hyderabad',
               'sports-injuries': 'sports-injuries-treatment', 'trigeminal-neuralgia': 'trigeminal-neuralgia-treatment',
               'elbow-hand-wrist': 'advanced-elbow-hand-and-wrist-pain-treatment',
               'foot-ankle-pain': 'foot-ankle-pain-treatment', 'cervical-spondylosis': 'cervical-spondylosis-treatment'}
TREAT_ANCHOR = {'regenerative-medicine': 'regenerative-medicine', 'radiofrequency-ablation': 'radiofrequency-ablations',
                'prolotherapy': 'prolotherapy', 'nerve-hydrodissection': 'non-surgical-nerve-hydrodissection-nerve-blocks'}

IMG = {  # topic -> photograph already on the site
    'knee-pain-treatment': 'knee-pain-treatment-hyderabad.webp',
    'low-back-pain-treatment': 'low-back-pain-treatment-hyderabad.webp',
    'neck-pain-treatment': 'neck-pain-treatment-hyderabad.webp',
    'shoulder-pain': 'shoulder-pain-treatment-hyderabad.webp',
    'sciatica': 'sciatica-treatment-hyderabad.webp',
    'slipped-disc-treatment': 'slipped-disc-treatment-hyderabad.webp',
    'the-best-hip-pain-treatment-in-hyderabad': 'hip-pain-treatment-hyderabad.webp',
    'sports-injuries-treatment': 'sports-injury-treatment-hyderabad.webp',
    'trigeminal-neuralgia-treatment': 'trigeminal-neuralgia-treatment-hyderabad.webp',
    'advanced-elbow-hand-and-wrist-pain-treatment': 'elbow-hand-wrist-pain-treatment-hyderabad.webp',
    'foot-ankle-pain-treatment': 'foot-ankle-pain-treatment-hyderabad.webp',
    'cervical-spondylosis-treatment': 'cervical-spondylosis-treatment-hyderabad.webp',
    'regenerative-medicine': 'regenerative-medicine-growth-factor-injection.webp',
    'radiofrequency-ablations': 'genicular-nerve-radiofrequency-ablation-knee-diagram.webp',
    'prolotherapy': 'prolotherapy-injection-knee.webp',
    'non-surgical-nerve-hydrodissection-nerve-blocks': 'nerve-hydrodissection-hand-nerve-pain.webp',
    'dr-d-pallavi-profile': 'dr-dasyam-pallavi-pain-specialist-hyderabad.webp',
    'dr-pss-kiran-profile': 'dr-pss-kiran-pain-specialist-hyderabad.webp',
}
IMG_ALT = {
    'regenerative-medicine': 'A growth factor concentrate injection being prepared',
    'radiofrequency-ablations': 'Diagram of genicular nerve radiofrequency ablation at the knee',
    'prolotherapy': 'A prolotherapy injection being placed at the knee',
    'non-surgical-nerve-hydrodissection-nerve-blocks': 'A hand held to show the path of an entrapped nerve',
    'dr-d-pallavi-profile': 'Dr. Dasyam Pallavi, consultant in pain management at Halcyon, Hyderabad',
    'dr-pss-kiran-profile': 'Dr. PSS Kiran, consultant radiologist in musculoskeletal imaging at Halcyon, Hyderabad',
}

HOME_FAQ = [  # the assistant's approved answers, shown on the page so they can be read and cited
    ('How do I book an appointment at Halcyon?',
     'Call +91 77880 91092 or +91 95536 04226 and the team will find you a slot. Bring any recent X-ray, MRI or ultrasound reports — they often save a second visit. You can also send them on WhatsApp before you come in.'),
    ('Where is Halcyon Pain Management Centre?',
     '3rd Floor, KKR Commercial Complex, at Kukatpally Y Junction on Moosapet Road, Hyderabad 500072 — above the Max showroom. It is a few minutes from the KPHB and Moosapet metro stations.'),
    ('What are the clinic timings?',
     'Monday to Saturday, 9 am to 6 pm; closed on Sunday. Appointments are spaced so the wait is short — call +91 77880 91092 for today’s slots.'),
    ('What happens on the day of my visit?',
     'Five steps in one appointment: you arrive and register, the consultant examines you, the painful joint or nerve is scanned by ultrasound in the same room, the findings decide the treatment, and if a procedure is right it is done there and then. Most people are home inside two hours.'),
    ('Will the procedure hurt, and will I be put to sleep?',
     'Procedures are done under local anaesthetic with ultrasound guidance, so you stay awake and talking throughout. There is no general anaesthetic and no hospital admission — you walk out the same day.'),
    ('Will I need surgery?',
     'Halcyon is a non-surgical centre — every procedure here is image-guided and done as day care. The one case where a replacement is still the right answer is advanced grade 4 knee arthritis with joint deformity, and you will be told that plainly rather than treated anyway.'),
    ('What will treatment cost?',
     'It depends on the procedure and how many sittings are needed, so the team gives you a clear figure at the consultation — before anything is booked. Call +91 77880 91092 and they can give you a range once they know what you are being treated for.'),
    ('Do you accept health insurance?',
     'That depends on your policy and the procedure. The team can tell you what applies to your case and what paperwork you would need — ask them when you call.'),
    ('What should I bring to my first appointment?',
     'Bring any recent X-ray, MRI, CT or ultrasound reports, a list of the medicines you take, and notes from any earlier treatment for the same pain. Tell the team when you book if you take blood thinners — they need planning before an injection.'),
    ('Who are the doctors at Halcyon?',
     'Dr. Dasyam Pallavi, Consultant – Pain Management (MBBS, DA, FIAPM, CIPS — Fellow of the Indian Academy of Pain Medicine; Certified Interventional Pain Sonologist, World Institute of Pain, USA), assesses you and performs the ultrasound-guided procedures. Dr. PSS Kiran, Consultant Radiologist – Musculoskeletal Imaging & Image Guidance (MBBS, MD Radiodiagnosis, Fellowship in Pain Management), provides musculoskeletal ultrasound evaluation, imaging correlation and image guidance, working with her.'),
]

CONTACT_FAQ = [
    ('Is there parking at the clinic?',
     'The clinic is in the KKR Commercial Complex at Kukatpally Y Junction. Call the team before you set out and they will tell you where it is easiest to park or be dropped off.'),
    ('How do I reach Halcyon by metro?',
     'The nearest stations are KPHB Colony and Moosapet on the Red Line, each a few minutes from Kukatpally Y Junction. The clinic is on the 3rd floor of the KKR Commercial Complex, above the Max showroom on Moosapet Road.'),
    ('Can I send my reports before the appointment?',
     'Yes. Send recent X-ray, MRI or ultrasound reports on WhatsApp to +91 77880 91092 and the team will look at them before your slot.'),
    ('Do I need a referral to see a pain specialist at Halcyon?',
     'No referral is needed. Call to book, and bring any reports and prescriptions you already have for the same pain.'),
]

# ============================================================================ helpers
esc = lambda s: html.escape(s, quote=True)

def slugify(s):
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')

def prefix(path):
    """relative prefix from a page's folder back to the site root"""
    return '../' * path.count('/') if path else ''

def home_href(path):
    return prefix(path) or './'

def split_title(h1):
    if ',' in h1:
        a, b = h1.split(',', 1)
        return a + ',', b.strip()
    return h1, ''

def read(f):
    return open(f, encoding='utf-8').read()

def write(f, s):
    os.makedirs(os.path.dirname(f) or '.', exist_ok=True)
    open(f, 'w', encoding='utf-8').write(s)

IMG_SIZE = {}
def img_size(name):
    if name not in IMG_SIZE:
        try:
            from PIL import Image
            IMG_SIZE[name] = Image.open('assets/img/' + name).size
        except Exception:
            IMG_SIZE[name] = None
    return IMG_SIZE[name]

# ============================================================================ page registry
def reg():
    P = []
    def add(**k):
        k.setdefault('crumbs', [])
        k.setdefault('image', 'assets/og/halcyon.jpg')
        k.setdefault('priority', '0.7')
        P.append(k)
    add(path='', file='index.html', kind='home', priority='1.0',
        title='Pain Management Centre in Hyderabad | Halcyon, Kukatpally',
        desc='Non-surgical, ultrasound-guided treatment for knee, back, neck, shoulder and nerve pain in Kukatpally, Hyderabad. Day care, local anaesthetic. Call 77880 91092.')
    add(path='services/', file='services/index.html', kind='hub-services', priority='0.9',
        title='Non-Surgical Pain Treatments in Hyderabad | Halcyon',
        desc='Regenerative medicine, cooled radiofrequency ablation, prolotherapy and nerve hydrodissection — image-guided, day-care pain treatments in Kukatpally, Hyderabad.',
        crumbs=[('Treatments', 'services/')])
    add(path='pain-conditions/', file='pain-conditions/index.html', kind='hub-conditions', priority='0.9',
        title='Pain Conditions Treated in Hyderabad | Halcyon',
        desc='Knee, back, neck, shoulder, sciatica, slipped disc, hip and nerve pain treated without surgery at Halcyon, Kukatpally — and the procedure used for each.',
        crumbs=[('Pain Conditions', 'pain-conditions/')])
    add(path='our-doctors/', file='our-doctors/index.html', kind='hub-doctors', priority='0.8',
        title='Pain Specialists in Hyderabad — Our Doctors | Halcyon',
        desc='Meet Dr. Dasyam Pallavi, consultant in pain management, and Dr. PSS Kiran, consultant radiologist for musculoskeletal imaging, at Halcyon, Kukatpally, Hyderabad.',
        crumbs=[('Our Doctors', 'our-doctors/')])
    add(path='about-us/', file='about-us/index.html', kind='about', priority='0.7',
        title='About Halcyon Pain Management Centre, Kukatpally',
        desc='A non-surgical pain centre in Kukatpally, Hyderabad, where the consultant who examines you also scans you and performs the procedure — in one appointment.',
        crumbs=[('About Us', 'about-us/')])
    add(path='contact/', file='contact/index.html', kind='contact', priority='0.8',
        title='Contact & Directions — Halcyon Pain Clinic, Kukatpally',
        desc='Halcyon Pain Management Centre, 3rd Floor, KKR Commercial Complex, Kukatpally Y Junction, Hyderabad 500072. Open Mon–Sat, 9 am–6 pm. Call +91 77880 91092.',
        crumbs=[('Contact', 'contact/')])
    add(path='privacy-policy/', file='privacy-policy/index.html', kind='privacy', priority='0.2',
        title='Privacy Policy | Halcyon Pain Management Centre',
        desc='How Halcyon Pain Management Centre handles your personal and health information, and what this website does and does not collect.',
        crumbs=[('Privacy Policy', 'privacy-policy/')])
    for s in COND_ORDER:
        d = CONDITIONS[s]
        add(path=s + '/', file=s + '/index.html', kind='condition', data=d, priority='0.9',
            title=d['title'], desc=d['meta_description'], image='assets/og/%s.jpg' % s,
            crumbs=[('Pain Conditions', 'pain-conditions/'), (d['name'], s + '/')])
    for s in TREAT_ORDER:
        d = TREATMENTS[s]
        add(path=s + '/', file=s + '/index.html', kind='treatment', data=d, priority='0.9',
            title=d['title'], desc=d['meta_description'], image='assets/og/%s.jpg' % s,
            crumbs=[('Treatments', 'services/'), (d['name'], s + '/')])
    for s in DOC_ORDER:
        d = DOCTORS[s]
        add(path=s + '/', file=s + '/index.html', kind='doctor', data=d, priority='0.8',
            title=d['title'], desc=d['meta_description'], image='assets/og/%s.jpg' % s,
            crumbs=[('Our Doctors', 'our-doctors/'), (d['name'], s + '/')])
    add(path='Halcyon-YourVisit-demo.html', file='Halcyon-YourVisit-demo.html', kind='noindex',
        title='Your Visit (demo) — Halcyon', desc='Earlier standalone demo of the visit timeline.')
    return P

PAGES = reg()
BY_PATH = {p['path']: p for p in PAGES}

# ============================================================================ JSON-LD
def address():
    return {'@type': 'PostalAddress', 'streetAddress': SITE['street'], 'addressLocality': SITE['city'],
            'addressRegion': SITE['region'], 'postalCode': SITE['postal'], 'addressCountry': SITE['country']}

def doctor_id(slug):
    return U + slug + '/#person'

def treat_id(slug):
    return U + slug + '/#procedure'

def cond_id(slug):
    return U + slug + '/#condition'

def clinic_node():
    return {
        '@type': 'MedicalClinic', '@id': ORG, 'name': SITE['name'], 'alternateName': SITE['alt_names'],
        'url': U, 'description': SITE['description'],
        'logo': {'@type': 'ImageObject', '@id': U + '#logo', 'url': U + 'assets/icons/icon-512.png',
                 'width': 512, 'height': 512, 'caption': SITE['name']},
        'image': [U + 'assets/og/halcyon.jpg', U + 'assets/img/knee-pain-non-surgical-treatment-halcyon-hyderabad.webp'],
        'telephone': SITE['tel_schema'], 'email': SITE['email'], 'address': address(),
        'geo': {'@type': 'GeoCoordinates', 'latitude': SITE['lat'], 'longitude': SITE['lng']},
        'hasMap': SITE['map'],
        'openingHoursSpecification': [{
            '@type': 'OpeningHoursSpecification',
            'dayOfWeek': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'],
            'opens': '09:00', 'closes': '18:00'}],
        'priceRange': '₹₹', 'currenciesAccepted': 'INR', 'paymentAccepted': 'Cash, Credit Card, Debit Card',
        'medicalSpecialty': ['Musculoskeletal', 'Anesthesia'],
        'isAcceptingNewPatients': True,
        'areaServed': [{'@type': 'City', 'name': 'Hyderabad'}] +
                      [{'@type': 'Place', 'name': a + ', Hyderabad'} for a in SITE['area_served'][1:]],
        'contactPoint': {'@type': 'ContactPoint', 'telephone': SITE['tel_schema'], 'contactType': 'appointments',
                         'areaServed': 'IN'},
        'availableService': [{'@id': treat_id(s)} for s in TREAT_ORDER],
        'employee': [{'@id': doctor_id(s)} for s in DOC_ORDER],
        'knowsAbout': [CONDITIONS[s]['name'] for s in COND_ORDER] + [TREATMENTS[s]['name'] for s in TREAT_ORDER],
        'sameAs': SITE['same_as'],
    }

def website_node():
    return {'@type': 'WebSite', '@id': WEBSITE, 'url': U, 'name': SITE['name'], 'alternateName': 'Halcyon',
            'publisher': {'@id': ORG}, 'inLanguage': 'en-IN'}

def doctor_node(slug, full=False):
    d = DOCTORS[slug]
    n = {'@type': 'Person', '@id': doctor_id(slug), 'name': d['name'], 'honorificPrefix': 'Dr.',
         'jobTitle': d['role'], 'worksFor': {'@id': ORG}, 'url': U + slug + '/',
         'image': U + 'assets/img/' + IMG[slug], 'description': d['summary'],
         'knowsAbout': d.get('knows_about', []) + [CONDITIONS[c]['name'] for c in d['conditions'] if c in CONDITIONS],
         'hasCredential': [
             dict({'@type': 'EducationalOccupationalCredential', 'name': c['name'],
                   'credentialCategory': 'certification' if re.search(r'Certif|Fellow', c['name']) else 'degree'},
                  **({'recognizedBy': {'@type': 'Organization', 'name': c['issuer']}} if c.get('issuer') else {}))
             for c in d['credentials']],
         }
    reg = d.get('registration')
    if reg:
        n['identifier'] = {'@type': 'PropertyValue', 'propertyID': reg['council'] + ' registration number',
                           'value': reg['number']}
    if any('Indian Academy of Pain Medicine' in c.get('issuer', '') for c in d['credentials']):
        n['memberOf'] = {'@type': 'Organization', 'name': 'Indian Academy of Pain Medicine'}
    return n

def treatment_node(slug):
    d = TREATMENTS[slug]; sc = d['schema']
    return {'@type': 'TherapeuticProcedure', '@id': treat_id(slug), 'name': d['name'],
            'alternateName': sc.get('alternate_names', []), 'url': U + slug + '/', 'description': d['summary'],
            'procedureType': 'https://schema.org/%sProcedure' % sc.get('procedure_type', 'Percutaneous'),
            'bodyLocation': ', '.join(sc.get('body_locations', [])),
            'howPerformed': sc.get('how_performed'), 'preparation': sc.get('preparation'),
            'followup': sc.get('followup')}

def condition_node(slug):
    d = CONDITIONS[slug]; sc = d['schema']
    n = {'@type': 'MedicalCondition', '@id': cond_id(slug), 'name': d['name'],
         'alternateName': sc.get('alternate_names', []), 'url': U + slug + '/', 'description': d['summary'],
         'associatedAnatomy': {'@type': 'AnatomicalStructure', 'name': sc.get('anatomy')},
         'signOrSymptom': [{'@type': 'MedicalSymptom', 'name': s} for s in sc.get('symptoms', [])],
         'cause': [{'@type': 'MedicalCause', 'name': s} for s in sc.get('causes', [])],
         'possibleTreatment': [{'@id': treat_id(t)} for t in d.get('treatments', [])] +
                              [{'@type': 'MedicalTherapy', 'name': t} for t in sc.get('possible_treatments', [])]}
    return n

def faq_node(url, faqs):
    return {'@type': 'FAQPage', '@id': url + '#faq', 'isPartOf': {'@id': url + '#webpage'},
            'mainEntity': [{'@type': 'Question', 'name': q,
                            'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in faqs]}

def breadcrumb_node(url, crumbs):
    items = [{'@type': 'ListItem', 'position': 1, 'name': 'Home', 'item': U}]
    for i, (name, path) in enumerate(crumbs):
        items.append({'@type': 'ListItem', 'position': i + 2, 'name': name, 'item': U + path})
    return {'@type': 'BreadcrumbList', '@id': url + '#breadcrumb', 'itemListElement': items}

PAGE_TYPE = {'home': 'MedicalWebPage', 'about': 'AboutPage', 'contact': 'ContactPage',
             'hub-services': 'CollectionPage', 'hub-conditions': 'CollectionPage', 'hub-doctors': 'CollectionPage',
             'condition': 'MedicalWebPage', 'treatment': 'MedicalWebPage', 'doctor': 'ProfilePage',
             'privacy': 'WebPage'}

def faqs_for(p):
    if p['kind'] in ('condition', 'treatment', 'doctor'):
        return [(f['q'], f['a']) for f in p['data']['faqs']]
    if p['kind'] == 'home':
        return HOME_FAQ
    if p['kind'] == 'contact':
        return CONTACT_FAQ
    return []

def graph(p):
    url = U + p['path']
    img = U + p['image']
    page = {'@type': PAGE_TYPE[p['kind']], '@id': url + '#webpage', 'url': url, 'name': p['title'],
            'description': p['desc'], 'isPartOf': {'@id': WEBSITE}, 'inLanguage': 'en-IN',
            'primaryImageOfPage': {'@type': 'ImageObject', 'url': img, 'width': 1200, 'height': 630},
            'dateModified': TODAY, 'publisher': {'@id': ORG}}
    nodes = [page, clinic_node(), website_node()]
    if p['crumbs']:
        page['breadcrumb'] = {'@id': url + '#breadcrumb'}
        nodes.append(breadcrumb_node(url, p['crumbs']))
    k = p['kind']
    if k == 'home':
        page['about'] = {'@id': ORG}
        page['audience'] = {'@type': 'MedicalAudience', 'audienceType': 'Patient'}
        nodes += [doctor_node(s) for s in DOC_ORDER] + [treatment_node(s) for s in TREAT_ORDER]
    elif k in ('about', 'contact', 'privacy'):
        page['about'] = {'@id': ORG}
        page['mainEntity'] = {'@id': ORG}
    elif k == 'hub-conditions':
        page['about'] = [{'@id': cond_id(s)} for s in COND_ORDER]
        page['hasPart'] = [{'@id': U + s + '/#webpage'} for s in COND_ORDER]
        nodes += [condition_node(s) for s in COND_ORDER]
        nodes.append(item_list(url, [(CONDITIONS[s]['name'], s) for s in COND_ORDER]))
    elif k == 'hub-services':
        page['about'] = [{'@id': treat_id(s)} for s in TREAT_ORDER]
        page['hasPart'] = [{'@id': U + s + '/#webpage'} for s in TREAT_ORDER]
        nodes += [treatment_node(s) for s in TREAT_ORDER]
        nodes.append(item_list(url, [(TREATMENTS[s]['name'], s) for s in TREAT_ORDER]))
    elif k == 'hub-doctors':
        page['about'] = [{'@id': doctor_id(s)} for s in DOC_ORDER]
        nodes += [doctor_node(s) for s in DOC_ORDER]
        nodes.append(item_list(url, [(DOCTORS[s]['name'], s) for s in DOC_ORDER]))
    elif k == 'condition':
        s = p['data']['slug']
        page['about'] = {'@id': cond_id(s)}; page['mainEntity'] = {'@id': cond_id(s)}
        page['audience'] = {'@type': 'MedicalAudience', 'audienceType': 'Patient'}
        page['specialty'] = 'https://schema.org/Musculoskeletal'
        nodes.append(condition_node(s))
        nodes += [treatment_node(t) for t in p['data'].get('treatments', []) if t in TREATMENTS]
    elif k == 'treatment':
        s = p['data']['slug']
        page['about'] = {'@id': treat_id(s)}; page['mainEntity'] = {'@id': treat_id(s)}
        page['audience'] = {'@type': 'MedicalAudience', 'audienceType': 'Patient'}
        # the conditions link back through MedicalCondition.possibleTreatment on their own pages
        page['mentions'] = [{'@id': cond_id(c)} for c in p['data'].get('conditions', []) if c in CONDITIONS]
        nodes.append(treatment_node(s))
    elif k == 'doctor':
        s = p['data']['slug']
        page['about'] = {'@id': doctor_id(s)}; page['mainEntity'] = {'@id': doctor_id(s)}
        nodes.append(doctor_node(s))
    f = faqs_for(p)
    if f:
        nodes.append(faq_node(url, f))
    return {'@context': 'https://schema.org', '@graph': nodes}

def item_list(url, items):
    return {'@type': 'ItemList', '@id': url + '#list', 'numberOfItems': len(items),
            'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'name': n, 'url': U + s + '/'}
                                for i, (n, s) in enumerate(items)]}

# ============================================================================ <head>
def seo_head(p, extra_css=''):
    pre = prefix(p['path'])
    url = U + p['path']
    img = U + p['image']
    og_type = {'doctor': 'profile', 'condition': 'article', 'treatment': 'article'}.get(p['kind'], 'website')
    robots = ('noindex, follow' if p['kind'] == 'noindex'
              else 'index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1')
    ld = json.dumps(graph(p), ensure_ascii=False, separators=(',', ':')) if p['kind'] != 'noindex' else ''
    out = ['<!-- seo:start — generated by tools/build.py; edit there, not here -->',
           '<title>%s</title>' % esc(p['title']),
           '<meta name="description" content="%s">' % esc(p['desc']),
           '<meta name="robots" content="%s">' % robots,
           '<link rel="canonical" href="%s">' % url]
    if p['kind'] != 'noindex':
        out += ['<link rel="alternate" hreflang="en-IN" href="%s">' % url,
                '<link rel="alternate" hreflang="x-default" href="%s">' % url]
    out += [
        '<meta name="author" content="%s">' % SITE['name'],
        '<meta name="theme-color" content="#2C0A1B">',
        '<meta name="geo.region" content="%s">' % SITE['region_code'],
        '<meta name="geo.placename" content="Kukatpally, Hyderabad">',
        '<meta name="geo.position" content="%s;%s">' % (SITE['lat'], SITE['lng']),
        '<meta name="ICBM" content="%s, %s">' % (SITE['lat'], SITE['lng']),
        '<meta property="og:type" content="%s">' % og_type,
        '<meta property="og:site_name" content="%s">' % SITE['name'],
        '<meta property="og:locale" content="en_IN">',
        '<meta property="og:title" content="%s">' % esc(p['title']),
        '<meta property="og:description" content="%s">' % esc(p['desc']),
        '<meta property="og:url" content="%s">' % url,
        '<meta property="og:image" content="%s">' % img,
        '<meta property="og:image:width" content="1200">',
        '<meta property="og:image:height" content="630">',
        '<meta property="og:image:alt" content="%s">' % esc(p['title']),
        '<meta name="twitter:card" content="summary_large_image">',
        '<meta name="twitter:title" content="%s">' % esc(p['title']),
        '<meta name="twitter:description" content="%s">' % esc(p['desc']),
        '<meta name="twitter:image" content="%s">' % img,
        '<link rel="icon" href="%sassets/icons/favicon.svg" type="image/svg+xml">' % pre,
        '<link rel="icon" href="%sassets/icons/favicon-32.png" sizes="32x32" type="image/png">' % pre,
        '<link rel="apple-touch-icon" href="%sassets/icons/apple-touch-icon.png">' % pre,
        '<link rel="manifest" href="%ssite.webmanifest">' % pre,
        '<link rel="preload" href="%sassets/fonts/dm-sans.woff2" as="font" type="font/woff2" crossorigin>' % pre,
        '<link rel="preload" href="%sassets/fonts/playfair-display-italic.woff2" as="font" type="font/woff2" crossorigin>' % pre,
    ]
    if ld:
        out.append('<script type="application/ld+json">%s</script>' % ld.replace('</', '<\\/'))
    if extra_css:
        out.append('<style>%s</style>' % extra_css)
    out.append('<!-- seo:end -->')
    return '\n'.join(out)

def inject_head(s, p, extra_css=''):
    block = seo_head(p, extra_css)
    s = re.sub(r'<html lang="[^"]*"', '<html lang="en-IN"', s, count=1)
    if '<!-- seo:start' in s:
        return re.sub(r'<!-- seo:start.*?<!-- seo:end -->', lambda m: block, s, count=1, flags=re.S)
    # first run on a hand-made page: drop what the block replaces
    head_end = s.find('</head>')
    head, rest = s[:head_end], s[head_end:]
    head = re.sub(r'\s*<title>.*?</title>', '', head, count=1, flags=re.S)
    head = re.sub(r'\s*<meta name="description"[^>]*>', '', head, count=1)
    head = re.sub(r'\s*<link rel="icon"[^>]*>', '', head)
    head = re.sub(r'(<meta name="viewport"[^>]*>)', lambda m: m.group(1) + '\n' + block, head, count=1)
    return head + rest

# ============================================================================ template parts
SRC = read('services/index.html')

def _between(s, a, b, start=0):
    i = s.index(a, start); j = s.index(b, i) + len(b)
    return s[i:j]

BASE_CSS = [m for m in re.findall(r'<style>(.*?)</style>', SRC, re.S) if ':root{' in m][0]
BODY = SRC[SRC.index('<body'):]
BIRD = _between(BODY, '<svg width="0" height="0"', '</svg>')
HEADER = _between(BODY, '<header class="nav"', '</header>')
FOOTER = _between(BODY, '<footer', '</footer>')
SCRIPT = [m for m in re.findall(r'<script>(.*?)</script>', BODY, re.S) if 'is-pill' in m][0]

def header_for(section):
    h = HEADER.replace(' class="is-here" aria-current="page"', '')
    h = h.replace('href="#top">Treatments', 'href="../services/">Treatments')
    label = {'condition': 'Pain Conditions', 'treatment': 'Treatments', 'doctor': 'Our Doctors',
             'contact': 'Contact'}.get(section)
    if label:
        h = re.sub(r'<a href="([^"]*)">%s</a>' % re.escape(label),
                   lambda m: '<a href="%s" class="is-here" aria-current="page">%s</a>' % (m.group(1), label), h, count=1)
    return h

ARROW = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h13M13 6l6 6-6 6"/></svg>'

PG_CSS = r'''
/* ==========================================================================
   Topic pages (generated by tools/build.py)
   ========================================================================== */
.crumbs{margin:0 0 22px}
.crumbs ol{margin:0; padding:0; list-style:none; display:flex; flex-wrap:wrap; justify-content:center; gap:6px 10px;
  font-size:13px; letter-spacing:.02em; color:rgba(251,227,237,.72)}
.crumbs li{display:flex; align-items:center; gap:10px}
.crumbs li + li::before{content:""; width:5px; height:5px; border-radius:50%; background:var(--rose-400); opacity:.7}
.crumbs a{border-bottom:1px solid transparent; transition:border-color .3s var(--ease), color .3s var(--ease)}
.crumbs a:hover{color:var(--cream); border-color:rgba(238,156,192,.5)}
.crumbs [aria-current]{color:var(--rose-200)}
.th__cta{margin:clamp(26px,4vh,38px) 0 0; display:flex; gap:12px; justify-content:center; flex-wrap:wrap}
.th.is-in .th__cta{transition-delay:.46s}
.th .btn--ghost{color:var(--cream)}

.pg{background:var(--cream); padding:clamp(48px,8vh,96px) var(--gut) clamp(24px,4vh,48px)}
.pg__grid{max-width:1180px; margin:0 auto; display:grid;
  grid-template-columns:minmax(0,1fr) minmax(280px,340px); gap:clamp(36px,5vw,76px); align-items:start}
.pg__main{min-width:0; max-width:760px}
.pg__lead{margin:0; padding:4px 0 4px 22px; border-left:3px solid var(--rose-400);
  font-size:19px; line-height:1.62; color:var(--charcoal)}
.pg__sec{margin:clamp(40px,6vh,60px) 0 0}
.pg__sec h2, .pg__block h2{margin:0; font-family:var(--serif); font-style:italic; font-weight:700;
  font-size:clamp(26px,2.5vw,34px); line-height:1.14; letter-spacing:-.01em; color:var(--rose-800)}
.pg__sec p{margin:16px 0 0; color:var(--charcoal); line-height:1.75}
.pg__sec ul, .pg__sec ol{margin:18px 0 0; padding:0; list-style:none; display:grid; gap:10px}
.pg__sec li{position:relative; padding-left:26px; color:var(--charcoal); line-height:1.6}
.pg__sec ul li::before{content:""; position:absolute; left:4px; top:.62em; width:8px; height:8px; border-radius:50%;
  background:var(--rose-400); box-shadow:0 0 0 4px rgba(221,101,158,.14)}
.pg__sec ol{counter-reset:step}
.pg__sec ol li{counter-increment:step; padding-left:40px}
.pg__sec ol li::before{content:counter(step); position:absolute; left:0; top:.05em; width:26px; height:26px;
  border-radius:50%; display:grid; place-items:center; font-size:12.5px; font-weight:700;
  background:var(--rose-100); color:var(--rose-700)}

.pg__block{margin:clamp(48px,7vh,72px) 0 0}
.pg__block > p{margin:14px 0 0; color:var(--muted)}
.tcards{margin:22px 0 0; display:grid; gap:14px}
.tcard{display:grid; grid-template-columns:96px minmax(0,1fr); gap:18px; align-items:center;
  padding:14px; border-radius:20px; background:#fff; border:1px solid var(--stone);
  transition:border-color .35s var(--ease), transform .35s var(--ease), box-shadow .35s var(--ease)}
.tcard:hover{border-color:var(--rose-300); transform:translateY(-2px); box-shadow:0 14px 34px -18px rgba(76,20,48,.4)}
.tcard img{width:96px; height:96px; object-fit:cover; border-radius:14px}
.tcard b{display:block; font-family:var(--serif); font-style:italic; font-size:21px; color:var(--rose-800); line-height:1.2}
.tcard span{display:block; margin-top:6px; font-size:14.5px; line-height:1.5; color:var(--muted)}
.chips{margin:20px 0 0; padding:0; list-style:none; display:flex; flex-wrap:wrap; gap:10px}
.chips a{display:inline-block; padding:10px 18px; border-radius:999px; font-size:14.5px; font-weight:500;
  background:#fff; border:1px solid var(--stone); color:var(--rose-800);
  transition:border-color .3s var(--ease), background .3s var(--ease)}
.chips a:hover{border-color:var(--rose-300); background:var(--rose-50)}

.faq{margin:22px 0 0; border-top:1px solid var(--stone)}
.faq details{border-bottom:1px solid var(--stone)}
.faq summary{list-style:none; cursor:pointer; display:flex; justify-content:space-between; gap:20px; align-items:center;
  padding:20px 2px; font-size:17.5px; font-weight:600; line-height:1.45; color:var(--ink)}
.faq summary::-webkit-details-marker{display:none}
.faq summary::after{content:""; flex:none; width:30px; height:30px; border-radius:50%;
  background:var(--rose-50) no-repeat center/12px
  url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 12 12'%3E%3Cpath d='M6 1v10M1 6h10' stroke='%237C2049' stroke-width='1.6' stroke-linecap='round'/%3E%3C/svg%3E");
  transition:transform .35s var(--ease), background-color .3s var(--ease)}
.faq details[open] summary::after{transform:rotate(45deg); background-color:var(--rose-100)}
.faq summary:hover{color:var(--rose-700)}
.faq details p{margin:0; padding:0 46px 22px 2px; color:var(--charcoal); line-height:1.72}

.pg__aside{align-self:stretch; display:flex; flex-direction:column; gap:18px}
.pg__aside > .card--book{position:sticky; top:104px}
.pg__fig{margin:0; border-radius:24px; overflow:hidden; background:var(--sand); aspect-ratio:4/5}
.pg__fig img{width:100%; height:100%; object-fit:cover}
.pg__fig--portrait{background:linear-gradient(158deg, var(--rose-800), var(--rose-900) 58%); display:flex; align-items:flex-end; justify-content:center}
.pg__fig--portrait img{height:auto; width:88%; object-fit:contain; filter:drop-shadow(0 22px 36px rgba(24,4,14,.5))}
.card{padding:22px 24px; border-radius:22px; background:#fff; border:1px solid var(--stone)}
.card h2, .card h3{margin:0 0 12px; font-size:11px; font-weight:700; letter-spacing:.16em; text-transform:uppercase; color:var(--muted)}
.facts{margin:0; display:grid; gap:14px}
.facts div{display:grid; gap:3px}
.facts dt{font-size:12.5px; font-weight:600; color:var(--rose-600)}
.facts dd{margin:0; font-size:15px; line-height:1.5; color:var(--ink)}
.toc{margin:0; padding:0; list-style:none; display:grid; gap:8px}
.toc a{font-size:14.5px; line-height:1.45; color:var(--charcoal); border-bottom:1px solid transparent; transition:color .3s var(--ease), border-color .3s var(--ease)}
.toc a:hover{color:var(--rose-700); border-color:var(--rose-200)}
.card--book{background:linear-gradient(152deg, var(--rose-700), var(--rose-900) 64%); border:0; color:var(--cream)}
.card--book h2, .card--book h3{color:var(--rose-200)}
.card--book p{margin:0 0 14px; font-size:15px; line-height:1.55; color:var(--rose-100)}
.card--book .btn{width:100%; justify-content:center}
.card--book .alt{margin:14px 0 0; display:flex; flex-wrap:wrap; gap:6px 16px; font-size:14px}
.card--book .alt a{color:var(--cream); border-bottom:1px solid rgba(238,156,192,.35)}
.card--book address{margin:14px 0 0; font-style:normal; font-size:13.5px; line-height:1.55; color:rgba(251,227,237,.78)}
.docs{display:grid; gap:12px}
.docs a{display:grid; grid-template-columns:52px minmax(0,1fr); gap:12px; align-items:center}
.docs img{width:52px; height:52px; border-radius:50%; object-fit:cover; object-position:top; background:var(--rose-100)}
.docs b{display:block; font-size:15px; color:var(--ink)}
.docs span{display:block; font-size:13px; color:var(--muted)}

.rel{background:var(--sand); padding:clamp(52px,8vh,96px) var(--gut)}
.rel__inner{max-width:1180px; margin:0 auto}
.rel__head{margin:0; font-family:var(--serif); font-style:italic; font-weight:700; font-size:clamp(26px,3vw,40px); color:var(--rose-800)}
.rel__grid{margin:28px 0 0; padding:0; list-style:none; display:grid; grid-template-columns:repeat(auto-fill,minmax(230px,1fr)); gap:18px}
.rel__grid a{display:block; border-radius:22px; overflow:hidden; background:#fff; border:1px solid var(--stone);
  transition:transform .35s var(--ease), box-shadow .35s var(--ease)}
.rel__grid a:hover{transform:translateY(-3px); box-shadow:0 18px 38px -22px rgba(76,20,48,.45)}
.rel__grid img{width:100%; aspect-ratio:4/3; object-fit:cover}
.rel__grid b{display:block; padding:16px 18px 4px; font-family:var(--serif); font-style:italic; font-size:21px; color:var(--rose-800)}
.rel__grid span{display:block; padding:0 18px 18px; font-size:14px; line-height:1.5; color:var(--muted)}

.visit{display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:16px; margin:24px 0 0}
.visit .card p, .visit .card address{margin:0; font-style:normal; line-height:1.65; color:var(--charcoal)}
.visit .card a{color:var(--rose-700); font-weight:600; border-bottom:1px solid var(--rose-200)}
.hours{width:100%; border-collapse:collapse; font-size:15px}
.hours td{padding:6px 0; border-bottom:1px dashed var(--stone)}
.hours td + td{text-align:right; font-weight:600}

@media (max-width:980px){
  .pg__grid{grid-template-columns:1fr}
  .pg__aside{display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); align-items:start}
  .pg__aside > .card--book{position:static}
  .pg__main{max-width:none}
  .pg__fig{aspect-ratio:16/10}
  .pg__fig--portrait{aspect-ratio:4/5; max-width:420px}
}
@media (max-width:640px){
  .visit{grid-template-columns:1fr}
  .pg__lead{font-size:17.5px}
  .faq details p{padding-right:4px}
}
'''

# ============================================================================ page bodies
def book_card(pre, heading='Book a consultation'):
    return f'''<section class="card card--book" aria-labelledby="book-h">
  <h2 id="book-h">{heading}</h2>
  <p>The examination and the diagnostic ultrasound happen in the same appointment.</p>
  <a class="btn btn--fill" href="tel:{SITE['tel']}">Call {SITE['tel_display']}</a>
  <p class="alt"><a href="https://wa.me/{SITE['wa']}" target="_blank" rel="noopener">WhatsApp us</a><a href="tel:{SITE['tel2']}">{SITE['tel2_display']}</a></p>
  <address>{SITE['street']}, {SITE['city']} {SITE['postal']}<br>{SITE['hours_text']}</address>
</section>'''

def doctors_card(pre, skip=None):
    items = []
    for s in DOC_ORDER:
        if s == skip:
            continue
        d = DOCTORS[s]
        items.append(f'<a href="{pre}{s}/"><img src="{pre}assets/img/{IMG[s]}" alt="" width="52" height="52" loading="lazy" decoding="async"><span><b>{esc(d["name"])}</b><span>{esc(d.get("short_role", d["credentials_line"]))}</span></span></a>')
    head = 'Also at Halcyon' if skip else 'Who will see you'
    return f'<section class="card"><h2>{head}</h2><div class="docs">{"".join(items)}</div></section>'

def sections_html(secs):
    out = []
    for s in secs:
        sid = slugify(s['h2'])
        ps = ''.join('<p>%s</p>' % esc(x) for x in s.get('paragraphs', []))
        bl = s.get('bullets') or []
        tag = 'ol' if re.search(r'step|procedure|on the day|what happens', s['h2'], re.I) and len(bl) > 2 else 'ul'
        ul = ('<%s>%s</%s>' % (tag, ''.join('<li>%s</li>' % esc(b) for b in bl), tag)) if bl else ''
        out.append(f'<section class="pg__sec" id="{sid}"><h2>{esc(s["h2"])}</h2>{ps}{ul}</section>')
    return '\n'.join(out)

def toc_html(secs, extra):
    items = [(slugify(s['h2']), s['h2']) for s in secs] + extra
    return '<nav class="card" aria-label="On this page"><h2>On this page</h2><ul class="toc">%s</ul></nav>' % ''.join(
        f'<li><a href="#{i}">{esc(t)}</a></li>' for i, t in items)

def faq_html(faqs, heading='Common questions'):
    items = ''.join(f'<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>' for q, a in faqs)
    return f'<section class="pg__block" id="faq"><h2>{esc(heading)}</h2><div class="faq">{items}</div></section>'

def crumbs_html(p):
    pre = prefix(p['path'])
    lis = ['<li><a href="%s">Home</a></li>' % home_href(p['path'])]
    for i, (n, path) in enumerate(p['crumbs']):
        if i == len(p['crumbs']) - 1:
            lis.append('<li aria-current="page">%s</li>' % esc(n))
        else:
            lis.append('<li><a href="%s%s">%s</a></li>' % (pre, path, esc(n)))
    return '<nav class="crumbs" aria-label="Breadcrumb"><ol>%s</ol></nav>' % ''.join(lis)

def hero(p, eyebrow, h1, sub, ghost=('#faq', 'Common questions')):
    l1, l2 = split_title(h1)
    l2h = f'<span class="l2">{esc(l2)}</span>' if l2 else ''
    return f'''<section class="th" id="top">
  <span class="th__wash" aria-hidden="true"></span>
  <svg class="th__bird" viewBox="0 0 400 330" aria-hidden="true"><use href="#bird"/></svg>
  <div class="th__inner">
    {crumbs_html(p)}
    <span class="eyebrow">{esc(eyebrow)}</span>
    <h1 class="th__title"><span class="l1">{esc(l1)}</span>{l2h}</h1>
    <p class="th__sub">{esc(sub)}</p>
    <div class="th__cta">
      <a href="tel:{SITE['tel']}" class="btn btn--fill">Book an appointment {ARROW}</a>
      <a href="{ghost[0]}" class="btn btn--ghost">{esc(ghost[1])}</a>
    </div>
  </div>
</section>'''

def cta(pre, title, text):
    return f'''<section class="cta" id="book">
  <div class="cta__inner">
    <h2 class="cta__t">{esc(title)}</h2>
    <p class="cta__p">{esc(text)}</p>
    <div class="cta__row">
      <a href="tel:{SITE['tel']}" class="btn btn--fill">Book an appointment {ARROW}</a>
      <a href="{pre}#jr" class="btn btn--ghost">What a visit looks like</a>
    </div>
    <p class="cta__num">
      <a href="tel:{SITE['tel']}">{SITE['tel_display']}</a>
      <a href="tel:{SITE['tel2']}">{SITE['tel2_display']}</a>
      <a href="mailto:{SITE['email']}">{SITE['email']}</a>
    </p>
  </div>
</section>'''

def figure(pre, slug, alt, portrait=False, eager=False):
    name = IMG[slug]
    sz = img_size(name) or (540, 720)
    load = 'fetchpriority="high"' if eager else 'loading="lazy"'
    cls = 'pg__fig pg__fig--portrait' if portrait else 'pg__fig'
    return f'<figure class="{cls}"><img src="{pre}assets/img/{name}" alt="{esc(alt)}" width="{sz[0]}" height="{sz[1]}" {load} decoding="async"></figure>'

def facts_card(facts):
    rows = ''.join(f'<div><dt>{esc(f["label"])}</dt><dd>{esc(f["value"])}</dd></div>' for f in facts)
    return f'<section class="card"><h2>At a glance</h2><dl class="facts">{rows}</dl></section>'

def rel_section(pre, heading, slugs, source):
    items = []
    for s in slugs:
        d = source[s]
        name = IMG[s]; sz = img_size(name) or (540, 720)
        blurb = d['summary'].split('. ')[0].rstrip('.') + '.'
        if len(blurb) > 150:
            blurb = blurb[:147].rsplit(' ', 1)[0] + '…'
        items.append(f'<li><a href="{pre}{s}/"><img src="{pre}assets/img/{name}" alt="" width="{sz[0]}" height="{sz[1]}" loading="lazy" decoding="async"><b>{esc(d["name"])}</b><span>{esc(blurb)}</span></a></li>')
    return f'<section class="rel" aria-labelledby="rel-h"><div class="rel__inner"><h2 class="rel__head" id="rel-h">{esc(heading)}</h2><ul class="rel__grid">{"".join(items)}</ul></div></section>'

def shell(p, section, body):
    head = seo_head(p)
    return f'''<!DOCTYPE html>
<html lang="en-IN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{head}
<style>{BASE_CSS}{PG_CSS}</style>
</head>
<body>
{BIRD}
{header_for(section)}
<main id="main">
{body}
</main>
{FOOTER}
<script>{SCRIPT}</script>
</body>
</html>
'''

def render_condition(p):
    d = p['data']; pre = prefix(p['path']); s = d['slug']
    tcards = ''.join(
        f'<a class="tcard" href="{pre}{t}/"><img src="{pre}assets/img/{IMG[t]}" alt="" width="96" height="96" loading="lazy" decoding="async"><span><b>{esc(TREATMENTS[t]["name"])}</b><span>{esc(TREATMENTS[t]["summary"].split(". ")[0].rstrip(".") + ".")}</span></span></a>'
        for t in d.get('treatments', []) if t in TREATMENTS)
    main = f'''<article class="pg__main">
  <p class="pg__lead">{esc(d['summary'])}</p>
  {sections_html(d['sections'])}
  <section class="pg__block" id="treatments"><h2>Treatments used for {esc(d['name'].lower())}</h2>
    <p>Which one is right is decided by what the scan shows, not chosen in advance.</p>
    <div class="tcards">{tcards}</div></section>
  {faq_html([(f['q'], f['a']) for f in d['faqs']], 'Questions about ' + d['name'].lower())}
</article>'''
    aside = f'''<aside class="pg__aside">
  {figure(pre, s, d['name'] + ' — assessed and treated at Halcyon, Hyderabad')}
  {facts_card(d['quick_facts'])}
  {doctors_card(pre)}
  {toc_html(d['sections'], [('treatments', 'Treatments used'), ('faq', 'Common questions')])}
  {book_card(pre)}
</aside>'''
    body = (hero(p, 'Pain Conditions', d['h1'],
                 'Examined and scanned by ultrasound in one appointment at Kukatpally — and, if a procedure is right, treated there and then under local anaesthetic.')
            + f'\n<div class="pg"><div class="pg__grid">{main}{aside}</div></div>\n'
            + rel_section(pre, 'Related conditions', [r for r in d.get('related', []) if r in CONDITIONS], CONDITIONS)
            + cta(pre, 'Find where it is actually coming from.',
                  'Book a consultation and the diagnostic ultrasound happens in the same appointment. Bring any recent X-ray, MRI or scan reports you already have.'))
    return shell(p, 'condition', body)

def render_treatment(p):
    d = p['data']; pre = prefix(p['path']); s = d['slug']
    chips = ''.join(f'<li><a href="{pre}{c}/">{esc(CONDITIONS[c]["name"])}</a></li>' for c in d.get('conditions', []) if c in CONDITIONS)
    main = f'''<article class="pg__main">
  <p class="pg__lead">{esc(d['summary'])}</p>
  {sections_html(d['sections'])}
  <section class="pg__block" id="conditions"><h2>Conditions it is used for</h2>
    <p>Each links to how that condition is assessed and treated at Halcyon.</p>
    <ul class="chips">{chips}</ul></section>
  {faq_html([(f['q'], f['a']) for f in d['faqs']], 'Questions about ' + d['name'].lower())}
</article>'''
    aside = f'''<aside class="pg__aside">
  {figure(pre, s, IMG_ALT.get(s, d['name']))}
  {facts_card(d['quick_facts'])}
  {doctors_card(pre)}
  {toc_html(d['sections'], [('conditions', 'Conditions it is used for'), ('faq', 'Common questions')])}
  {book_card(pre)}
</aside>'''
    body = (hero(p, 'Treatments', d['h1'],
                 'Image-guided, under local anaesthetic, as day care — and chosen by what the diagnostic scan shows, not from a menu.')
            + f'\n<div class="pg"><div class="pg__grid">{main}{aside}</div></div>\n'
            + rel_section(pre, 'The other treatments at Halcyon', [r for r in d.get('related', []) if r in TREATMENTS], TREATMENTS)
            + cta(pre, 'The scan decides which one.',
                  'Book a consultation and the diagnostic ultrasound happens in the same appointment. Bring any recent X-ray, MRI or scan reports you already have.'))
    return shell(p, 'treatment', body)

def render_doctor(p):
    d = p['data']; pre = prefix(p['path']); s = d['slug']
    conds = ''.join(f'<li><a href="{pre}{c}/">{esc(CONDITIONS[c]["name"])}</a></li>' for c in d['conditions'] if c in CONDITIONS)
    treats = ''.join(f'<li><a href="{pre}{t}/">{esc(TREATMENTS[t]["name"])}</a></li>' for t in d['treatments'] if t in TREATMENTS)
    creds = [{'label': 'Qualifications', 'value': d['credentials_line']}, {'label': 'Role', 'value': d['role']}]
    if d.get('registration'):
        creds.append({'label': 'Registration', 'value': 'Regd. No. %s — %s' % (d['registration']['number'], d['registration']['council'])})
    creds.append({'label': 'Consults at', 'value': 'Kukatpally Y Junction, Hyderabad — by appointment'})
    main = f'''<article class="pg__main">
  <p class="pg__lead">{esc(d['summary'])}</p>
  {sections_html(d['sections'])}
  <section class="pg__block" id="conditions"><h2>{esc(d.get('conditions_heading', 'Conditions treated'))}</h2>
    <ul class="chips">{conds}</ul></section>
  <section class="pg__block" id="treatments"><h2>{esc(d.get('treatments_heading', 'Treatments performed'))}</h2>
    <ul class="chips">{treats}</ul></section>
  {faq_html([(f['q'], f['a']) for f in d['faqs']])}
</article>'''
    aside = f'''<aside class="pg__aside">
  {figure(pre, s, IMG_ALT[s], portrait=True, eager=True)}
  {facts_card(creds).replace('At a glance', 'Credentials')}
  {doctors_card(pre, skip=s)}
  {book_card(pre, 'Book an appointment')}
</aside>'''
    body = (hero(p, 'Our Doctors', d['h1'], d['role'] + '. ' + d['hero_sub'])
            + f'\n<div class="pg"><div class="pg__grid">{main}{aside}</div></div>\n'
            + cta(pre, 'The examination and the imaging, read together.',
                  'Book a consultation and the diagnostic ultrasound happens in the same appointment. Bring any recent X-ray, MRI or scan reports you already have.'))
    return shell(p, 'doctor', body)

def render_contact(p):
    pre = prefix(p['path'])
    main = f'''<article class="pg__main">
  <p class="pg__lead">Halcyon Pain Management Centre is on the 3rd floor of the KKR Commercial Complex at Kukatpally Y Junction, Moosapet Road, Hyderabad 500072 — above the Max showroom, a few minutes from the KPHB and Moosapet metro stations. Call {SITE['tel_display']} to book.</p>
  <div class="visit">
    <section class="card" id="address"><h2>Address</h2>
      <address>{SITE['name']}<br>{SITE['street']}<br>{SITE['area']}, {SITE['city']}, {SITE['region']} {SITE['postal']}<br>India</address>
      <p style="margin-top:14px"><a href="{SITE['map']}" target="_blank" rel="noopener">Open in Google Maps</a></p></section>
    <section class="card" id="hours"><h2>Opening hours</h2>
      <table class="hours"><tbody>
        <tr><td>Monday – Saturday</td><td>9:00 am – 6:00 pm</td></tr>
        <tr><td>Sunday</td><td>Closed</td></tr></tbody></table></section>
    <section class="card" id="phone"><h2>Call or message</h2>
      <p><a href="tel:{SITE['tel']}">{SITE['tel_display']}</a> &nbsp;·&nbsp; <a href="tel:{SITE['tel2']}">{SITE['tel2_display']}</a></p>
      <p style="margin-top:10px"><a href="https://wa.me/{SITE['wa']}" target="_blank" rel="noopener">WhatsApp {SITE['tel_display']}</a></p>
      <p style="margin-top:10px"><a href="mailto:{SITE['email']}">{SITE['email']}</a></p></section>
    <section class="card" id="landmark"><h2>Finding us</h2>
      <p>{esc(SITE['landmark'])}</p></section>
  </div>
  <section class="pg__sec" id="before-you-come"><h2>Before you come</h2>
    <p>Call ahead so the team can give you a slot and tell you roughly how long the visit will take. Most procedures are day care, and you go home the same day.</p>
    <ul><li>Bring any recent X-ray, MRI, CT or ultrasound reports.</li>
        <li>Bring a list of the medicines you take, and notes from any earlier treatment for the same pain.</li>
        <li>If you take blood thinners, say so when you book — they need planning before an injection. Do not stop any medicine on your own.</li></ul></section>
  {faq_html(CONTACT_FAQ)}
</article>'''
    aside = f'''<aside class="pg__aside">
  {book_card(pre, 'Book an appointment')}
  {doctors_card(pre)}
</aside>'''
    body = (hero(p, 'Contact', 'Visit Halcyon, at Kukatpally Y Junction', SITE['hours_text'] + ' Call ' + SITE['tel_display'] + ' to book.',
                 ghost=(SITE['map'], 'Get directions'))
            + f'\n<div class="pg"><div class="pg__grid">{main}{aside}</div></div>\n'
            + cta(pre, 'Bring the reports. We will bring the scanner.',
                  'The examination and the diagnostic ultrasound happen in the same appointment, and if a procedure is right, it is done there and then.'))
    return shell(p, 'contact', body)

RENDER = {'condition': render_condition, 'treatment': render_treatment, 'doctor': render_doctor,
          'contact': render_contact}

# ============================================================================ hand-made pages
HUB_CSS = '''
.cd__name a{color:inherit; border-bottom:1px solid transparent; transition:border-color .3s var(--ease)}
.cd__name a:hover{border-color:currentColor}
.cd__more, .tx__more, .dr__more{display:inline-flex; align-items:center; gap:8px; margin-top:14px; font-size:14.5px; font-weight:600;
  color:var(--rose-600); border-bottom:1px solid var(--rose-200); padding-bottom:2px; transition:color .3s, border-color .3s}
.cd__more:hover, .tx__more:hover, .dr__more:hover{color:var(--rose-800); border-color:var(--rose-400)}
.dr__more{color:var(--rose-200); border-color:rgba(238,156,192,.35)}
.dr__more:hover{color:var(--cream); border-color:var(--rose-300)}
'''
HOME_FAQ_CSS = '''
.hfaq{background:var(--cream); padding:clamp(64px,10vh,120px) var(--gut)}
.hfaq__inner{max-width:900px; margin:0 auto}
.hfaq__head{margin:0; text-align:center; font-family:var(--serif); font-style:italic; font-weight:700;
  font-size:clamp(30px,3.6vw,50px); line-height:1.08; letter-spacing:-.014em; color:var(--rose-800)}
.hfaq__sub{margin:16px auto 0; max-width:560px; text-align:center; color:var(--muted)}
.hfaq .faq{margin-top:clamp(28px,4vh,44px); border-top:1px solid var(--stone)}
.hfaq details{border-bottom:1px solid var(--stone)}
.hfaq summary{list-style:none; cursor:pointer; display:flex; justify-content:space-between; gap:20px; align-items:center;
  padding:22px 2px; font-size:18px; font-weight:600; line-height:1.45; color:var(--ink)}
.hfaq summary::-webkit-details-marker{display:none}
.hfaq summary::after{content:""; flex:none; width:32px; height:32px; border-radius:50%;
  background:var(--rose-50) no-repeat center/12px
  url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 12 12'%3E%3Cpath d='M6 1v10M1 6h10' stroke='%237C2049' stroke-width='1.6' stroke-linecap='round'/%3E%3C/svg%3E");
  transition:transform .35s var(--ease)}
.hfaq details[open] summary::after{transform:rotate(45deg)}
.hfaq details p{margin:0; padding:0 50px 24px 2px; color:var(--charcoal); line-height:1.72}
'''

def home_faq_html():
    items = ''.join(f'<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>' for q, a in HOME_FAQ)
    return ('<!-- faq:start — generated by tools/build.py -->\n<section class="hfaq" id="faq" aria-labelledby="hfaq-h">'
            '<div class="hfaq__inner"><h2 class="hfaq__head" id="hfaq-h">Questions people ask before they come in</h2>'
            '<p class="hfaq__sub">The short answers. Anything else, the team will tell you on the phone.</p>'
            f'<div class="faq">{items}</div></div></section>\n<!-- faq:end -->\n')

def footer_links(s, path):
    """footers copied between pages carry in-page anchors (#prolotherapy); point them at the topic pages"""
    pre = prefix(path)
    anchors = dict(TREAT_ANCHOR, **COND_ANCHOR)
    anchors['nerve-blocks'] = 'non-surgical-nerve-hydrodissection-nerve-blocks'
    def one(m):
        return re.sub(r'href="#([a-z-]+)"', lambda a: 'href="%s%s/"' % (pre, anchors[a.group(1)]) if a.group(1) in anchors else a.group(0), m.group(0))
    return re.sub(r'<footer.*?</footer>', one, s, flags=re.S)

def fix_images(s, path):
    """every content image gets its real dimensions, so nothing shifts as it loads"""
    pre = prefix(path)
    def one(m):
        tag = m.group(0)
        src = re.search(r'src="([^"]+)"', tag)
        if not src or 'assets/img/' not in src.group(1):
            return tag
        name = src.group(1).split('assets/img/')[1]
        sz = img_size(name)
        if sz and 'width=' not in tag:
            tag = tag.replace('<img ', '<img width="%d" height="%d" ' % sz, 1)
        if 'decoding=' not in tag:
            tag = tag.replace('<img ', '<img decoding="async" ', 1)
        return tag
    return re.sub(r'<img\b[^>]*>', one, s)

def upgrade_home(s):
    # the hero is the largest thing on screen: fetch it first, never lazily
    s = re.sub(r'(<img )(src="assets/img/knee-pain-non-surgical-treatment-halcyon-hyderabad\.webp")',
               lambda m: m.group(0) if 'fetchpriority' in s[m.start():m.start()+300] else m.group(1) + 'fetchpriority="high" ' + m.group(2), s, count=1)
    # pillar photographs repeat the treatments beside them; describe them for people who can't see them
    for label, alt in [('Regenerative Medicine', 'Growth factor concentrate being prepared for a regenerative injection'),
                       ('Radiofrequency Ablation', 'Diagram of radiofrequency ablation of the genicular nerves at the knee'),
                       ('Prolotherapy', 'A prolotherapy injection being placed at the knee'),
                       ('Nerve Hydrodissection', 'A hand held to show the path of an entrapped nerve')]:
        s = re.sub(r'(data-label="%s">\s*<img[^>]*?)alt=""' % re.escape(label), lambda m: m.group(1) + 'alt="%s"' % alt, s, count=1)
    s = re.sub(r'alt="Dr\. Dasyam Pallavi[^"]*"( loading="lazy">)', lambda m: 'alt="%s"%s' % (IMG_ALT['dr-d-pallavi-profile'], m.group(1)), s)
    s = re.sub(r'alt="Dr\. PSS Kiran[^"]*"( loading="lazy">)', lambda m: 'alt="%s"%s' % (IMG_ALT['dr-pss-kiran-profile'], m.group(1)), s)
    # doctor cards -> profile pages
    for name, slug in [('Dr. Dasyam Pallavi', 'dr-d-pallavi-profile'), ('Dr. PSS Kiran', 'dr-pss-kiran-profile')]:
        pat = r'(<h3 class="dr__name">%s</h3>(?:(?!</article>).)*?)(\s*</div>\s*</article>)' % re.escape(name)
        s = re.sub(pat, lambda m: m.group(0) if 'dr__more' in m.group(1) else
                   m.group(1) + '\n          <a class="dr__more" href="%s/">View full profile %s</a>' % (slug, ARROW) + m.group(2),
                   s, count=1, flags=re.S)
    # the first patient story is in the HTML, so it can be read without running the script
    m = re.search(r"var REVIEWS = \[\s*\[\s*'((?:[^'\\]|\\.)*)'\s*,\s*'((?:[^'\\]|\\.)*)'", s)
    if m and '<blockquote id="tmQuote"></blockquote>' in s:
        q = m.group(1).replace("\\'", "'"); n = m.group(2).replace("\\'", "'")
        s = s.replace('<blockquote id="tmQuote"></blockquote>', '<blockquote id="tmQuote">%s</blockquote>' % esc(q), 1)
        s = s.replace('<b id="tmName"></b>', '<b id="tmName">%s</b>' % esc(n), 1)
    # visible FAQ, just above the footer
    block = home_faq_html()
    if '<!-- faq:start' in s:
        s = re.sub(r'<!-- faq:start.*?<!-- faq:end -->\n', lambda m: block, s, count=1, flags=re.S)
    else:
        s = s.replace('<!-- ============ FOOTER ============ -->', block + '\n<!-- ============ FOOTER ============ -->', 1)
    return s

def upgrade_conditions_hub(s):
    for anchor, slug in COND_ANCHOR.items():
        name = CONDITIONS[slug]['name']
        s = re.sub(r'(<li class="cd__card" id="%s"(?:(?!</li>).)*?<h3 class="cd__name">)([^<]+)(</h3>)' % anchor,
                   lambda m: '%s<a href="../%s/">%s</a>%s' % (m.group(1), slug, m.group(2), m.group(3)), s, count=1, flags=re.S)
        s = re.sub(r'(<li class="cd__card" id="%s"(?:(?!</li>).)*?<p class="cd__tag">[^<]*</p>)(\s*</div>)' % anchor,
                   lambda m: m.group(0) if 'cd__more' in m.group(0) else
                   m.group(1) + '\n          <a class="cd__more" href="../%s/">Read the full guide to %s %s</a>' % (slug, esc(name.lower()), ARROW) + m.group(2),
                   s, count=1, flags=re.S)
    return s

def upgrade_services_hub(s):
    for anchor, slug in TREAT_ANCHOR.items():
        name = TREATMENTS[slug]['name']
        s = re.sub(r'(<section class="tx[^"]*" id="%s">(?:(?!</section>).)*?<p class="tx__para">(?:(?!</p>).)*</p>)' % anchor,
                   lambda m: m.group(0) if 'tx__more' in s[m.end():m.end()+200] else
                   m.group(1) + '\n      <a class="tx__more" href="../%s/">Read the full guide to %s %s</a>' % (slug, esc(name.lower()), ARROW),
                   s, count=1, flags=re.S)
    return s

def upgrade_doctors_hub(s):
    for anchor, slug, short in [('pallavi', 'dr-d-pallavi-profile', 'Dr. Pallavi'), ('kiran', 'dr-pss-kiran-profile', 'Dr. Kiran')]:
        s = re.sub(r'(<section class="pf[^"]*" id="%s">(?:(?!</section>).)*?<div class="pf__cta">(?:(?!</div>).)*?)(\s*</div>)' % anchor,
                   lambda m: m.group(0) if 'Full profile' in m.group(1) else
                   m.group(1) + '\n        <a class="pf__link" href="../%s/">Full profile of %s</a>' % (slug, short) + m.group(2),
                   s, count=1, flags=re.S)
    return s

UPGRADE = {'home': upgrade_home, 'hub-conditions': upgrade_conditions_hub, 'hub-services': upgrade_services_hub,
           'hub-doctors': upgrade_doctors_hub}
EXTRA_CSS = {'home': HUB_CSS + HOME_FAQ_CSS, 'hub-conditions': HUB_CSS, 'hub-services': HUB_CSS}

# ============================================================================ plain-text views
def page_text(s):
    b = s[s.find('<main') if '<main' in s else s.find('</header>'):]
    b = b[:b.find('<footer')] if '<footer' in b else b
    b = re.sub(r'<(script|style|svg|noscript)\b.*?</\1>', '', b, flags=re.S)
    b = re.sub(r'<[^>]*aria-hidden="true"[^>]*>.*?</(span|div)>', '', b, flags=re.S)
    b = re.sub(r'<h([1-3])[^>]*>', lambda m: '\n\n' + '#' * (int(m.group(1)) + 1) + ' ', b)
    b = re.sub(r'</h[1-3]>', '\n', b)
    b = re.sub(r'<summary[^>]*>', '\n\n**', b); b = b.replace('</summary>', '**\n')
    b = re.sub(r'<li[^>]*>', '\n- ', b)
    b = re.sub(r'<(p|br|div|dt|tr|blockquote)[^>]*>', '\n', b)
    b = html.unescape(re.sub(r'<[^>]+>', ' ', b))
    b = re.sub(r'[ \t]+', ' ', b)
    b = re.sub(r' *\n *', '\n', b)
    b = re.sub(r'\n{3,}', '\n\n', b)
    return b.strip()

# ============================================================================ site files
def write_site_files(texts):
    urls = []
    for p in PAGES:
        if p['kind'] == 'noindex':
            continue
        imgs = []
        if p['kind'] in ('condition', 'treatment', 'doctor'):
            imgs.append((U + 'assets/img/' + IMG[p['data']['slug']], p['data']['name']))
        imgs.append((U + p['image'], p['title']))
        img_xml = ''.join('<image:image><image:loc>%s</image:loc><image:title>%s</image:title></image:image>' % (esc(i), esc(t)) for i, t in imgs)
        urls.append('<url><loc>%s</loc><lastmod>%s</lastmod><changefreq>monthly</changefreq><priority>%s</priority>%s</url>'
                    % (U + p['path'], TODAY, p['priority'], img_xml))
    write('sitemap.xml', '<?xml version="1.0" encoding="UTF-8"?>\n'
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
          'xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n' + '\n'.join(urls) + '\n</urlset>\n')

    bots = '\n\n'.join('User-agent: %s\nAllow: /' % b for b in AI_BOTS)
    write('robots.txt', f'''# Halcyon Pain Management Centre — {U}
# Every search engine and AI assistant is welcome to read and cite this site.
# The one page kept out of results is an old demo, and it carries its own noindex.

User-agent: *
Allow: /

# Named explicitly so the permission is unambiguous for each crawler.
{bots}

Sitemap: {U}sitemap.xml
''')

    def line(p):
        return '- [%s](%s%s): %s' % (p['title'].split(' | ')[0], U, p['path'], p['desc'])
    llms = [f'# {SITE["name"]}', '',
            f'> {SITE["description"]}', '',
            '## Key facts', '',
            f'- Address: {SITE["street"]}, {SITE["area"]}, {SITE["city"]}, {SITE["region"]} {SITE["postal"]}, India',
            f'- Landmark: {SITE["landmark"]}',
            f'- Phone (appointments): {SITE["tel_display"]}; also {SITE["tel2_display"]}. WhatsApp: {SITE["tel_display"]}',
            f'- Email: {SITE["email"]}',
            f'- Hours: {SITE["hours_text"]}',
            f'- Map: {SITE["map"]}',
            '- Doctors: Dr. Dasyam Pallavi — Consultant, Pain Management; MBBS, DA, FIAPM (Fellow, Indian Academy of Pain Medicine), CIPS (Certified Interventional Pain Sonologist, World Institute of Pain, USA); TSMC Reg. No. 61959; performs the ultrasound-guided procedures. Dr. PSS Kiran — Consultant Radiologist, Musculoskeletal Imaging & Image Guidance; MBBS, MD (Radiodiagnosis), Fellowship in Pain Management, additional training in musculoskeletal ultrasound; TSMC Reg. No. 62201; imaging evaluation and image guidance, in collaboration with Dr. Pallavi.',
            '- How it works: the consultant who examines you scans you with diagnostic ultrasound and, if a procedure is right, performs it in the same appointment. Procedures are image-guided, under local anaesthetic, as day care — no general anaesthesia and no admission; most people are home within about two hours.',
            '- Non-surgical: the one case where a replacement is still advised is advanced grade 4 knee arthritis with deformity.',
            '- Costs are given at consultation, before anything is booked.', '',
            '## Pain conditions treated', ''] + [line(BY_PATH[s + '/']) for s in COND_ORDER] + [
            '', '## Treatments', ''] + [line(BY_PATH[s + '/']) for s in TREAT_ORDER] + [
            '', '## Doctors', ''] + [line(BY_PATH[s + '/']) for s in DOC_ORDER] + [
            '', '## The clinic', ''] + [line(BY_PATH[k]) for k in ('', 'about-us/', 'services/', 'pain-conditions/', 'our-doctors/', 'contact/')] + [
            '', '## Optional', '', line(BY_PATH['privacy-policy/']),
            f'- [Full text of every page]({U}llms-full.txt): the whole site as plain text, for assistants that prefer one file', '']
    write('llms.txt', '\n'.join(llms))

    full = [f'# {SITE["name"]} — full site text', '',
            f'Source: {U} · Updated {TODAY} · Phone {SITE["tel_display"]} · {SITE["street"]}, {SITE["city"]} {SITE["postal"]}', '']
    for p in PAGES:
        if p['kind'] == 'noindex' or p['path'] not in texts:
            continue
        full += ['', '---', '', f'URL: {U}{p["path"]}', f'Title: {p["title"]}', '', texts[p['path']]]
    write('llms-full.txt', '\n'.join(full) + '\n')

    write('site.webmanifest', json.dumps({
        'name': SITE['name'], 'short_name': 'Halcyon', 'start_url': './', 'scope': './', 'display': 'standalone',
        'background_color': '#FBF8F9', 'theme_color': '#2C0A1B', 'lang': 'en-IN',
        'description': SITE['description'],
        'icons': [{'src': 'assets/icons/icon-192.png', 'sizes': '192x192', 'type': 'image/png'},
                  {'src': 'assets/icons/icon-512.png', 'sizes': '512x512', 'type': 'image/png'},
                  {'src': 'assets/icons/icon-512-maskable.png', 'sizes': '512x512', 'type': 'image/png', 'purpose': 'maskable'}]},
        indent=2, ensure_ascii=False) + '\n')

    links = ''.join('<li><a href="/%s/">%s</a></li>' % (s, esc(CONDITIONS[s]['name'])) for s in COND_ORDER)
    write('404.html', f'''<!DOCTYPE html>
<html lang="en-IN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Page not found — {SITE['name']}</title>
<meta name="robots" content="noindex">
<link rel="icon" href="/assets/icons/favicon.svg" type="image/svg+xml">
<style>
body{{margin:0;min-height:100vh;display:grid;place-items:center;background:#2C0A1B;color:#FBF8F9;
  font:17px/1.6 system-ui,-apple-system,"Segoe UI",sans-serif;padding:40px 20px;box-sizing:border-box}}
main{{max-width:640px;text-align:center}}
h1{{font:italic 700 clamp(32px,6vw,54px)/1.08 Georgia,serif;margin:0}}
p{{color:#FBE3ED}} a{{color:#EE9CC0}}
ul{{list-style:none;padding:0;display:flex;flex-wrap:wrap;gap:10px;justify-content:center;margin:26px 0}}
li a{{display:inline-block;padding:9px 16px;border:1px solid rgba(238,156,192,.35);border-radius:999px;text-decoration:none}}
.btn{{display:inline-block;margin-top:10px;padding:14px 26px;border-radius:999px;background:#BF3872;color:#fff;text-decoration:none;font-weight:600}}
</style>
</head>
<body>
<main>
<h1>That page has moved or no longer exists.</h1>
<p>Everything from the old site is still here, under clearer addresses. Start from what hurts:</p>
<ul>{links}</ul>
<p><a class="btn" href="/">Go to the home page</a></p>
<p>Or call <a href="tel:{SITE['tel']}">{SITE['tel_display']}</a> and the team will help.</p>
</main>
</body>
</html>
''')

# ============================================================================ Open Graph images
def og_images():
    need, seen = [], set()
    for p in PAGES:  # one image per file; the shared default takes the home page's title
        if p['kind'] != 'noindex' and p['image'] not in seen and not os.path.exists(p['image']):
            need.append(p)
        seen.add(p['image'])
    if not need:
        return
    import io
    from PIL import Image, ImageDraw, ImageFont
    from fontTools.ttLib import TTFont
    def ttf(path):
        f = TTFont(path); f.flavor = None; b = io.BytesIO(); f.save(b); b.seek(0); return b
    serif = ttf('assets/fonts/playfair-display-italic.woff2').getvalue()
    sans = ttf('assets/fonts/dm-sans.woff2').getvalue()
    os.makedirs('assets/og', exist_ok=True)
    W, H = 1200, 630
    for p in need:
        im = Image.new('RGB', (W, H), (44, 10, 27))
        d = ImageDraw.Draw(im)
        # soft rose glow, like the site's hero wash
        glow = Image.new('L', (W, H), 0); gd = ImageDraw.Draw(glow)
        for r in range(420, 0, -6):
            gd.ellipse((180 - r, 700 - r, 180 + r, 700 + r), fill=int(70 * (1 - r / 420)))
        im = Image.composite(Image.new('RGB', (W, H), (191, 56, 114)), im, glow)
        d = ImageDraw.Draw(im)
        slug = p.get('data', {}).get('slug') if p.get('data') else None
        photo = IMG.get(slug) if slug else 'knee-pain-non-surgical-treatment-halcyon-hyderabad.webp'
        if photo:
            ph = Image.open('assets/img/' + photo).convert('RGBA')
            pw = 470
            if p['kind'] == 'doctor':
                ph.thumbnail((pw, H - 40)); x = W - ph.width - 50; y = H - ph.height
                im.paste(ph, (x, y), ph)
            else:
                ratio = max(pw / ph.width, H / ph.height)
                ph = ph.resize((int(ph.width * ratio) + 1, int(ph.height * ratio) + 1))
                l = (ph.width - pw) // 2; t = (ph.height - H) // 2
                ph = ph.crop((l, t, l + pw, t + H))
                mask = Image.new('L', (pw, H), 255)
                md = ImageDraw.Draw(mask)
                for i in range(120):
                    md.line([(i, 0), (i, H)], fill=int(255 * i / 120))
                im.paste(ph.convert('RGB'), (W - pw, 0), mask)
        d = ImageDraw.Draw(im)
        f_kick = ImageFont.truetype(io.BytesIO(sans), 24); f_kick.set_variation_by_axes([700]) if hasattr(f_kick, 'set_variation_by_axes') else None
        f_t = ImageFont.truetype(io.BytesIO(serif), 62)
        f_s = ImageFont.truetype(io.BytesIO(sans), 27)
        d.text((72, 70), 'HALCYON  ·  PAIN MANAGEMENT CENTRE', font=f_kick, fill=(238, 156, 192))
        title = p['title'].split(' | ')[0].split(' — ')[0]
        if p['kind'] == 'home':
            title = 'Live life pain-free.'
        words = title.split(); lines = []; cur = ''
        for w in words:
            t = (cur + ' ' + w).strip()
            if d.textlength(t, font=f_t) > 620 and cur:
                lines.append(cur); cur = w
            else:
                cur = t
        lines.append(cur)
        y = 150
        for ln in lines[:4]:
            d.text((72, y), ln, font=f_t, fill=(251, 248, 249)); y += 76
        sub = 'Non-surgical · Ultrasound-guided · Day care'
        d.text((72, y + 22), sub, font=f_s, fill=(251, 227, 237))
        d.text((72, H - 92), 'Kukatpally Y Junction, Hyderabad', font=f_s, fill=(92, 198, 208))
        d.text((72, H - 56), 'Call ' + SITE['tel_display'], font=f_s, fill=(251, 248, 249))
        im.save(p['image'], 'JPEG', quality=84, optimize=True, progressive=True)

# ============================================================================ main
def main():
    og_images()
    texts = {}
    for p in PAGES:
        if p['kind'] in RENDER:
            s = RENDER[p['kind']](p)
        else:
            if not os.path.exists(p['file']):
                print('missing', p['file']); continue
            s = read(p['file'])
            if p['kind'] in UPGRADE:
                s = UPGRADE[p['kind']](s)
            s = inject_head(s, p, EXTRA_CSS.get(p['kind'], ''))
        s = footer_links(fix_images(s, p['path']), p['path'])
        write(p['file'], s)
        texts[p['path']] = page_text(s)
    write_site_files(texts)
    print('built %d pages; sitemap has %d URLs' % (len(PAGES), sum(1 for p in PAGES if p['kind'] != 'noindex')))

if __name__ == '__main__':
    main()
