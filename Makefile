# XXX have a Makefile written by someone that knows Makefiles...

NAME=refine-client-py
VERSION = 0.1

SMALL_TEST_FILES = google/test/test_refine_small.py google/test/test_facet.py google/test/test_history.py 
LARGE_TEST_FILES = google/test/test_refine.py google/test/test_tutorial.py
TEST_FILES = $(SMALL_TEST_FILES) $(LARGE_TEST_FILES)

SOURCE = google/*.py google/refine/*.py google/test/*.py
TEST_DATA = google/test/data/*.csv
BUMF = README.rst Makefile
ALL = $(SOURCE) $(TEST_DATA) $(BUMF)

readme:
	rst2html.py README.rst > README.html

test:
	PYTHONPATH=. sh -c 'for t in $(TEST_FILES); do python $$t; done'

smalltest:
	PYTHONPATH=. sh -c 'for t in $(SMALL_TEST_FILES); do python $$t; done'

clean:
	find . -name '*.pyc' | xargs rm -f
	rm -f README.html

# COPYFILE_DISABLE=true for annoying ._* files in OS X
dist: clean
	(cd ..; COPYFILE_DISABLE=true tar zcf $(NAME)-$(VERSION).tar.gz  --exclude='.*' $(NAME))
