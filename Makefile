PIPY_URL ?= https://upload.pypi.org/legacy/
TOKEN ?=
VERSION := $(shell cat VERSION | tr -d '\n')

version:
	sed "s/_VERSION_/'"$(VERSION)"'/g" pyproject.toml > pyproject.tmp && mv pyproject.tmp pyproject.toml
	echo "Version set to $(VERSION)"

proto: version
	uv sync --dev
	# grpcio-tools is pinned out of the project env on Python >= 3.14 (no
	# cp314 wheel for 1.71.2, and 1.75.1 needs protobuf 6 while the runtime
	# stays on 5.29.x). Generate the pb2 sources through an isolated uvx
	# environment on 3.13 instead, so protoc runs the same way regardless of
	# which interpreter make itself is invoked under (tox runs make build
	# inside every py311..py314 env).
	uvx --from "grpcio-tools==1.71.2" --python 3.13 \
		python -m grpc_tools.protoc -Iamaas/grpc/protos=./protos \
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
