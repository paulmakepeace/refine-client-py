# XXX have a Makefile written by someone that knows Makefiles...

all: test build install

readme:
	# requires docutils, e.g. pip install docutils
	rst2html.py README.rst > README.html
	w3m -dump README.html | unix2dos > README.txt

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
	rm -rf README.{html,txt} build dist refine_client.egg-info distribute-*

upload: clean
	python setup.py sdist upload
	
