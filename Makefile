PIPY_URL ?= https://upload.pypi.org/legacy/
TOKEN ?=
VERSION := $(shell cat VERSION | tr -d '\n')

version:
	sed "s/_VERSION_/'"$(VERSION)"'/g" pyproject.toml > pyproject.tmp && mv pyproject.tmp pyproject.toml
	echo "Version set to $(VERSION)"

proto: version
	uv sync --dev
	uv run python -m grpc_tools.protoc -Iamaas/grpc/protos=./protos \
		--python_out=. \
		--pyi_out=. \
		--grpc_python_out=. \
		./protos/scan.proto

build: proto
	uv run python -m build --sdist --wheel

test: proto
	uv run pytest tests

upload:
	uv run twine upload --repository-url $(PIPY_URL) -u __token__ -p $(TOKEN) ./dist/*.whl --skip-existing

clean:
	@rm -rf dist build *.egg-info amaas/grpc/protos/
