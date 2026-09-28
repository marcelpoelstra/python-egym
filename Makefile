
build: clean
	python -m build

clean:

	rm -fr build
	rm -fr dist
	rm -fr python_egym.egg-info
	find . -path ./.venv -prune -o -name '__pycache__' -type d -exec rm -rf {} +

