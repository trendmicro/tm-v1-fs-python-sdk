from setuptools import setup, find_namespace_packages

with open("README.md", "r") as fh:
    long_description = fh.read()
with open("public/VERSION", "r") as fh:
    _version = fh.read().strip()
setup(
    name="amaas-grpc",
    version=_version,
    author="Trend Micro Team San Jose",
    description="Project AMaaS >_",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://www.trendmicro.com/",
    packages=find_namespace_packages(where="public", exclude=["tests*", "examples"]),
    package_dir={"": "public"},
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: Other/Proprietary License",
    ],
    python_requires=">=3.9",
)

