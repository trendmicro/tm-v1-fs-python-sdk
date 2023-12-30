PIPY_URL ?= https://upload.pypi.org/legacy/
TOKEN ?=
VERSION := $(shell cat VERSION | tr -d '\n')

proto:
	pipenv sync --dev
	pipenv run python -m grpc_tools.protoc -Iamaas/grpc/protos=./protos \
		--python_out=. \
		--pyi_out=. \
		--grpc_python_out=. \
		./protos/scan.proto

build: proto
	pipenv run pipenv-setup sync
	pipenv run python setup.py sdist bdist_wheel

test: proto
	pipenv run pytest tests

upload:
	pipenv run twine upload --repository-url $(PIPY_URL) -u __token__ -p $(TOKEN) ./dist/*.whl --skip-existing

clean:
	@rm -rf dist build *.egg-info amaas/grpc/protos/
