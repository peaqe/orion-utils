.PHONY: test/lint
test/lint:
	rm -rf /tmp/ovenv
	python3.8 -m venv /tmp/ovenv
	/tmp/ovenv/bin/pip install -r test_requirements.txt
	/tmp/ovenv/bin/flake8 .


.PHONY: test/units
test/units:
	rm -rf /tmp/ovenv
	python3.8 -m venv /tmp/ovenv
	/tmp/ovenv/bin/pip install .
	/tmp/ovenv/bin/pip install pyyaml
	/tmp/ovenv/bin/pip install -r test_requirements.txt
	/tmp/ovenv/bin/coverage run --source=orionutils -m pytest --capture=no --verbose test/units
	/tmp/ovenv/bin/coverage report -m
