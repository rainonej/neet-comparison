# NEET question bank

The repository currently includes a provenance-aware sample bank drawn from the official **NEET-UG 2020 English booklet E1**:

- `data/question_bank/neet_2020_e1_sample_questions.json`
- `data/question_bank/neet_2020_e1_sample_questions.csv`
- `reports/interactive/question-bank.json` — browser-ready curated set (24 items, answers matched to the final E1 key) loaded by the visual essay

## Why this bank exists

The public visual essay needs one genuine examination item to make the knife-edge argument concrete. The question should not be treated as proof that scientific knowledge is irrelevant to medicine. The narrower and defensible point is:

> An item can validly test syllabus knowledge without directly measuring the full qualities that make someone a good doctor, while a correct, wrong or blank response can still alter rank and affordable-seat options.

The featured item is **English booklet E1, question 21**:

> The specific palindromic sequence which is recognized by EcoRI is:

The correct option is **A / (1): 5′–GAATTC–3′ / 3′–CTTAAG–5′**.

It was selected because it is:

- a normal, valid syllabus item rather than a disputed or broken question;
- easy to verify in the official paper (E1 PDF page 4);
- built from near-identical letter strings that are easy to scramble under time pressure, including for readers with dyslexia;
- a clear example of biotechnology recall that does not itself observe clinical judgment, communication, ethics, reliability or care.

## Provenance

Official NTA source page:

- https://neet.nta.nic.in/document/english-set-e1-neet-qp-2020/

Official English E1 PDF:

- https://cdnbbsr.s3waas.gov.in/s37bc1ec1d9c3426357e69acd5bf320061/uploads/2022/02/2022021555.pdf

The featured EcoRI item was checked against the official NTA English E1 PDF as question 21 on page 4, with option order matching the supplied scan. Chemistry items 101, 104 and 107 were also aligned by number and wording. The remaining sample items in `data/question_bank/` came from the user-supplied extraction package; their exact E1 question numbers remain intentionally blank until aligned against the source booklet.

## Scoring distinction

For the 2020 paper format used in the essay:

- correct answer: **+4**;
- wrong answer: **−1**;
- blank: **0**.

Therefore:

- correct versus blank is a **four-mark** gap;
- correct versus wrong is a **five-mark** gap;
- a blind four-option guess has expected value `0.25 × 4 + 0.75 × (−1) = +0.25` marks.

The essay’s “within ±1 answer” crowd estimate uses a four-mark correct-answer equivalent. It is not an individual counselling-cutoff claim.

## Rights and reuse

The repository stores only a limited sample for research, criticism and source indexing. It does not embed the full 180-question paper or claim ownership of the examination text. Underlying rights remain with the source publisher. Future imports should retain source URLs, booklet codes, answer-key provenance and verification status.

## Future schema work

A full bank should add:

- exact official question number for every item;
- paper/page coordinates;
- final-answer-key row and version;
- subject and topic checked against booklet order;
- image dependency or formula-rendering requirements;
- whether multiple correct answers were accepted;
- a stable hash of normalized question text;
- editorial tags such as `featured`, `face_validity_example`, and `requires_diagram`.
