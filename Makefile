RUNS ?= 5

.PHONY: run

# complete evaluation
run:
	uv run record.py --runs $(RUNS)
	uv run record.py --runs $(RUNS) --policy-in system
	uv run judge.py policy-in-user policy-in-system
	uv run score.py policy-in-user policy-in-system --detail > scores.txt
