# XXX have a Makefile written by someone that knows Makefiles...

SMALL_TEST_FILES = google/test/test_refine_small.py google/test/test_facet.py google/test/test_history.py 
LARGE_TEST_FILES = google/test/test_refine.py google/test/test_tutorial.py
TEST_FILES = $(SMALL_TEST_FILES) $(LARGE_TEST_FILES)

test: $(TEST_FILES)
	PYTHONPATH=. sh -c 'for t in $(TEST_FILES); do python $$t; done'

smalltest: $(SMALL_TEST_FILES)
	PYTHONPATH=. sh -c 'for t in $(SMALL_TEST_FILES); do python $$t; done'
