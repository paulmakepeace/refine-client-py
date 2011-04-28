# XXX have a Makefile written by someone that knows Makefiles...

NAME = refine-client-py
# make sure VERSION matches what's in setup.py
VERSION = 0.1.0

all: test build install
	
readme:
	# requires docutils, e.g. pip install docutils
	rst2html.py README.rst > README.html

test:
	python setup.py test

# tests that don't require a Refine server running
smalltest:
	python setup.py test --test-suite tests.test_refine_small
	python setup.py test --test-suite tests.test_facet
	python setup.py test --test-suite tests.test_history

build:
	python setup.py build
	
install:
	sudo python setup.py install

clean:
	find . -name '*.pyc' | xargs rm -f
	# XXX is there some way of having setup.py clean up its junk?
	rm -rf README.html build dist refine_client_py.egg-info distribute-*

# COPYFILE_DISABLE=true for annoying ._* files in OS X
dist: clean
	(cd ..; COPYFILE_DISABLE=true tar zcf $(NAME)-$(VERSION).tar.gz  --exclude='.*' $(NAME))
