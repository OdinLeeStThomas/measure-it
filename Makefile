.PHONY: run

# score policy-in-user fixtures with per-slice detail
run:
	uv run python score.py policy-in-user --detail > output.txt
