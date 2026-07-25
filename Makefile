.PHONY: audit status test summarize bayes privilege

audit:
	python scripts/audit_catalog.py

status:
	python scripts/build_source_status.py

test:
	pytest -q

summarize:
	python scripts/summarize_neet_2024_marks.py

bayes:
	python scripts/run_bayesian_model.py

privilege:
	python scripts/run_privilege_inequality.py
