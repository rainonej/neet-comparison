# Privacy and lawful data handling

This project seeks statistical evidence, not personal dossiers.

## Permitted acquisition routes

- official public releases;
- open research repositories;
- data shared by authors under appropriate terms;
- registration-gated or licensed datasets obtained through the normal process;
- public RTI replies and lawful archives;
- deidentified or aggregated administrative extracts;
- commercial datasets purchased or licensed for research use.

## Prohibited routes

- credential sharing or bypassing a login/paywall;
- soliciting hacked, stolen, or unlawfully disclosed records;
- retaining unnecessary candidate names, dates of birth, addresses, phone numbers, roll numbers, or application numbers;
- joining public lists to identify or profile individual students;
- redistributing restricted microdata contrary to its license.

A person's citizenship does not create a right to bypass Indian access controls or privacy law. A public-record theory may support requesting information, but it does not automatically legalize any copy found online.

## Process for identifiable public lists

Only use such files when necessary to derive aggregate admissions statistics. Run an ingestion step that drops direct identifiers before the data enter `data/processed/`. Suppress or pool small cells. Keep a provenance record without preserving the identifiers.

## Author-shared research data

Ask the author to confirm:

- that the shared file is deidentified;
- the permitted research purpose;
- whether redistribution is allowed;
- the citation and acknowledgement terms;
- whether ethics approval or a data-use agreement is required.

When raw sharing is impossible, request a custom cross-tabulation or ask the author to run supplied analysis code.
