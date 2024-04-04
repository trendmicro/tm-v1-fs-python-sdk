from setuptools import setup, find_namespace_packages

with open("README.md", "r") as fh:
    long_description = fh.read()
with open("VERSION", "r") as fh:
    package_version = fh.read().strip()
setup(
    name="visionone-filesecurity",
    version=package_version,
    author="Trend Micro VisionOne File Security Team",
    description="Trend Micro VisionOne File Security SDK for python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/trendmicro/tm-v1-fs-python-sdk",
    packages=find_namespace_packages(exclude=["tests*", "examples"]),
    package_data={"amaas": ["grpc/protos/*"]},
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
    ],
    python_requires=">=3.7"
)

