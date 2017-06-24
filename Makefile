
build: clean
	python setup.py check
	python setup.py sdist
	python setup.py bdist

clean:

	rm -fr build
	rm -fr dist
	rm -fr python_egym.egg-info
	find . -name '*.pyc' -exec rm -f {} \;
	find . -name '*.pyo' -exec rm -f {} \;

