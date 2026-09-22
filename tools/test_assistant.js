#!/usr/bin/env node
/* Checks the assistant's matching against real-world phrasings.
   Run after `python3 tools/build.py`:   node tools/test_assistant.js
   Each case: [what someone types, the entry id (or kind:…) it must land on]. */
'use strict';
const path = require('path');
const fs = require('fs');
const root = path.join(__dirname, '..');
global.window = {};
eval(fs.readFileSync(path.join(root, 'assets/js/assistant-kb.js'), 'utf8'));
const { Engine, THRESH } = require(path.join(root, 'assets/js/assistant.js'));
const kb = global.window.HALCYON_KB;
const eng = Engine(kb);

const CASES = [
  // logistics
  ['how do i book an appointment', 'book'], ['i want appointment', 'book'], ['appoinment kavali', 'book'],
  ['please call me back', 'callback'], ['where is your clinic', 'where'], ['address please', 'where'],
  ['clinic location kukatpally', 'where'], ['how to reach by metro', 'metro'], ['nearest metro station', 'metro'],
  ['is there parking', 'parking'], ['what are your timings', 'timings'], ['are you open on sunday', 'sunday'],
  ['what time do you close', 'timings'], ['how much does it cost', 'cost'], ['fees kitna hai', 'cost'],
  ['treatment charges', 'cost'], ['consultation fee', 'consult-fee'], ['do you accept insurance', 'insurance'],
  ['is cashless available', 'cashless'], ['what should i bring', 'bring'], ['can i send my mri on whatsapp', 'reports-online'],
  ['what happens on the first visit', 'first-visit'], ['how long will the appointment take', 'howlong-visit'],
  ['do i need to fast before the procedure', 'fasting'], ['can i drive after the injection', 'drive'],
  ['when can i go back to work', 'work'], ['do you do video consultation', 'online-consult'],
  ['do you have a lady doctor', 'lady-doctor'], ['do you treat children', 'children'], ['whatsapp number', 'whatsapp'],
  ['email id', 'email'], ['i want to talk to a person', 'human'],
  // procedures & safety
  ['will i need surgery', 'surgery'], ['doctor told me knee replacement', 'knee-replacement-advised'],
  ['is it painful', 'anaesthesia'], ['will you put me to sleep', 'anaesthesia'], ['i am scared of needles', 'needle-fear'],
  ['how many sessions will i need', 'sessions'], ['is it permanent', 'permanent'], ['what is the success rate', 'success-rate'],
  ['any side effects', 'side-effects'], ['is it safe', 'safety'], ['is it a steroid injection', 'steroids'],
  ['what is radiofrequency ablation', 'rfa'], ['what is coolief', 'coolief'], ['what is prp', 'prp'],
  ['stem cell therapy', 'stem-cell'], ['what is prolotherapy', 'prolotherapy'], ['what is hydrodissection', 'hydrodissection'],
  ['epidural injection for back', 'epidural'], ['medial branch block', 'medial-branch-block'],
  ['do i need an mri first', 'mri-first'], ['ultrasound or mri which is better', 'ultrasound-vs-mri'],
  ['i take blood thinners', 'blood-thinners'], ['i am diabetic', 'diabetes'], ['i am pregnant', 'pregnancy'],
  ['can i take painkillers', 'painkillers'], ['physiotherapy along with treatment', 'physio'],
  // doctors
  ['who are the doctors', 'doctors'], ['tell me about dr pallavi', 'dr-pallavi'], ['who is dr kiran', 'dr-kiran'],
  ['what is cips', 'cips'], ['how many years of experience', 'experience'], ['who does the procedure', 'who-does-procedure'],
  ['why is there a radiologist', 'why-radiologist'],
  // conditions — English, typos, Tenglish / Hinglish
  ['i have knee pain', 'knee'], ['kneee pain', 'knee'], ['mokallu noppi', 'knee'], ['ghutno me dard', 'knee'],
  ['my lower back hurts', 'low-back'], ['kamar dard', 'low-back'], ['nadumu noppi', 'low-back'],
  ['neck pain', 'neck'], ['meda noppi', 'neck'], ['gardan me dard', 'neck'], ['shoulder pain', 'shoulder'],
  ['frozen shoulder', 'frozen-shoulder'], ['cant lift my arm', 'kind:condition'], ['rotator cuff tear', 'rotator-cuff'],
  ['sciatica', 'sciatica'], ['siatica pain', 'sciatica'], ['pain going down my leg', 'kind:condition'],
  ['slipped disc', 'slipped-disc'], ['disc bulge l4 l5', 'disc-bulge|slipped-disc'], ['herniated disc', 'kind:condition'],
  ['hip pain', 'hip'], ['sports injury', 'sports'], ['tennis elbow', 'tennis-elbow'], ['carpal tunnel', 'carpal-tunnel'],
  ['wrist pain', 'elbow-hand-wrist'], ['heel pain in the morning', 'kind:condition'], ['plantar fasciitis', 'plantar-fasciitis'],
  ['ankle sprain', 'ankle-sprain'], ['trigeminal neuralgia', 'trigeminal'], ['face pain like electric shock', 'trigeminal'],
  ['cervical spondylosis', 'cervical-spondylosis'], ['spondylitis', 'cervical-spondylosis'], ['arthritis in knee', 'knee-oa'],
  ['meniscus tear', 'meniscus'], ['acl injury', 'acl-ligament'], ['numbness in leg', 'leg-numbness'],
  ['pain radiating to arm', 'arm-radiating'], ['piriformis', 'piriformis'], ['spinal stenosis', 'stenosis'],
  ['tailbone pain', 'tailbone'], ['achilles tendon pain', 'achilles'],
  // off-scope — honest answers
  ['migraine', 'migraine'], ['diabetic neuropathy', 'diabetic-neuropathy'], ['gout', 'gout'],
  ['toothache', 'dental-pain'], ['stomach pain', 'abdominal-pain'],
  // emergencies must always win
  ['i cant control my bladder and my back hurts', 'kind:urgent'], ['numbness between my legs', 'kind:urgent'],
  ['chest pain', 'kind:urgent'], ['my face is drooping and speech is slurred', 'kind:urgent'],
  ['fell from bike and cant walk', 'kind:urgent'], ['worst headache of my life', 'kind:urgent'],
  ['back pain with fever', 'kind:urgent'], ['leg getting weaker every day', 'kind:urgent'],
  // small talk
  ['hi', 'greeting'], ['namaskaram', 'greeting'], ['thank you', 'thanks'], ['bye', 'bye'],
  ['are you a robot', 'bot'], ['telugu lo matladandi', 'language'],
  // a page's own FAQ wins when the question is specific; the overview wins when it is not
  ['how long does prolotherapy take to work', 'prolotherapy-faq-6'], ['can knee pain be treated without surgery', 'knee-pain-treatment-faq-1'],
  ['what is prolotherapy', 'prolotherapy'], ['does dr pallavi do the injection', 'dr-pallavi|who-does-procedure'],
  // greetings wrapped around a real question answer the question
  ['hi my knee hurts', 'knee'], ['ok what is the cost', 'cost'], ['hello doctor i have back pain', 'low-back'],
];

/* ordinary worries that must NOT get the emergency answer */
const CALM = ['back pain', 'my back hurts when i sit', 'knee pain after a fall last year', 'neck pain and headache',
  'leg pain', 'i have fever and body pain', 'my knee is swollen', 'shoulder pain for months', 'heel pain',
  'numbness in fingers', 'back pain for 2 years', 'is the injection painful'];

let pass = 0, fail = [];
for (const [q, want] of CASES) {
  const r = eng.rank(q);
  const top = r[0];
  const ok = top && top.s >= THRESH.maybe &&
    (want.startsWith('kind:') ? top.e.kind === want.slice(5) || (want === 'kind:urgent' && r.some(x => x.e.kind === 'urgent' && x.phrase >= THRESH.urgent)) : want.split('|').includes(top.e.id));
  if (ok) pass++;
  else fail.push(`  ✗ "${q}" → wanted ${want}, got ${top ? top.e.id + ' (' + top.s.toFixed(1) + ')' : 'nothing'}` +
                 (r[1] ? `, then ${r[1].e.id} (${r[1].s.toFixed(1)})` : ''));
}
for (const q of CALM) {
  const r = eng.rank(q);
  if (r.some(x => x.e.kind === 'urgent' && x.phrase >= THRESH.urgent)) fail.push(`  ✗ "${q}" → wrongly treated as an emergency`);
  else pass++;
}
console.log(fail.join('\n'));
console.log(`${pass}/${CASES.length + CALM.length} passed`);
process.exit(fail.length ? 1 : 0);
