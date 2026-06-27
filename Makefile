.PHONY: test reproduce fixtures docker judge-package judge

PYTHON ?= .venv/bin/python

fixtures:
	$(PYTHON) scripts/build_synthetic_fixtures.py

test: fixtures
	SVAMITVA_CONFIG_PATH=config/platform_config.synthetic.json $(PYTHON) -m pytest

reproduce: fixtures
	SVAMITVA_CONFIG_PATH=config/platform_config.synthetic.json bash scripts/reproduce.sh

judge-package:
	SVAMITVA_CONFIG_PATH=config/platform_config.synthetic.json $(PYTHON) scripts/generate_judge_package.py --train

judge:
	bash scripts/judge_verify.sh

docker:
	docker build -t svamitva-api .
