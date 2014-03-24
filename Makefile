PYTHON_MODULES := django_atomic_celery tests
PYTHON_SCRIPTS := setup.py testrunner.py
PYTHON_MODULES_AND_SCRIPTS := ${PYTHON_MODULES} ${PYTHON_SCRIPTS}
PYTHON_BIN := python
FLAKE8_BIN := flake8
FLAKE8_FLAGS := --ignore=W601

all:

test:
	@${PYTHON_BIN} testrunner.py
	@${FLAKE8_BIN} ${FLAKE8_FLAGS} ${PYTHON_MODULES_AND_SCRIPTS}

stylecheck:
	@${FLAKE8_BIN} ${FLAKE8_FLAGS} ${PYTHON_MODULES_AND_SCRIPTS}

publish:
	@${PYTHON_BIN} setup.py sdist upload

clean:
	@find ${PYTHON_MODULES} -name '*.pyc' | xargs rm -f
	@rm -f "$(addsuffix c,${PYTHON_SCRIPTS})"

.PHONY: test stylecheck publish clean
