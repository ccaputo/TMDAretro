PIP=./env/bin/pip2
PYTEST=./env/bin/pytest
PYTEST_ARGS=-v --timeout=60 -x --full-trace
TEST_NONAUTH=test-cookie.py test-urlsplit.py test-pending.py test-ofmipd.py
TEST_AUTH=test-ofmipd-auth.py

env:
	virtualenv --python=python2 env
	$(PIP) install -e .

test: env pytest-install
	cd test && ../$(PYTEST) $(PYTEST_ARGS) $(TEST_NONAUTH)

testauth: env pytest-install
	cd test && ../$(PYTEST) $(PYTEST_ARGS) $(TEST_AUTH)

testf: env pytest-install
	cd test && ../$(PYTEST) --failed $(PYTEST_ARGS) $(TEST_NONAUTH)

testfauth: env pytest-install
	cd test && ../$(PYTEST) --failed $(PYTEST_ARGS) $(TEST_AUTH)

testf-clean: env clean-testf pytest-install
	cd test && ../$(PYTEST) --failed $(PYTEST_ARGS) $(TEST_NONAUTH)

testfauth-clean: env clean-testf pytest-install
	cd test && ../$(PYTEST) --failed $(PYTEST_ARGS) $(TEST_AUTH)

testall: test testauth

pytest-install:
	if [ ! -f $(PYTEST) ]; then \
		$(PIP) install pytest ;\
		$(PIP) install pytest-runfailed ;\
		$(PIP) install pytest-timeout ;\
	fi

clean-testf:
	rm -rf test/.pytest

clean: clean-testf
	rm -rf env build dist TMDAretro.egg-info
	find . -name __pycache__ | xargs rm -rf
	find . -name .pytest_cache | xargs rm -rf
	find . -name \*.pyc | xargs rm -f

wheel:
	python2 setup.py bdist_wheel

release:
	@if git tag | grep -q TMDAretro-`python2 setup.py -V` ; then\
		echo "Already released this version.";\
		echo "Update the version number and try again.";\
		exit 1;\
	fi
	# python2 setup.py bdist_wheel upload
	# python2 setup.py sdist --formats=zip,gztar,bztar upload
	# git tag TMDAretro-`python2 setup.py -V`
	# git push
	# git push --tags
