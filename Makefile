.PHONY: audit status test summarize

audit:
	python scripts/audit_catalog.py

status:
	python scripts/build_source_status.py

test:
	pytest -q

summarize:
	python scripts/summarize_neet_2024_marks.py
