.PHONY: audit status test summarize bayes privilege score-privilege mospi mospi-extended

audit:
	python scripts/audit_catalog.py

status:
	python scripts/build_source_status.py

test:
	pytest -q

summarize:
	python scripts/summarize_neet_2024_marks.py

mospi:
	python scripts/process_mospi_priority.py

mospi-extended:
	python scripts/process_mospi_extended.py

bayes:
	python scripts/run_bayesian_model.py

privilege:
	python scripts/run_privilege_inequality.py

score-privilege:
	python scripts/run_score_privilege.py
