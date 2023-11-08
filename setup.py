import re
from os.path import abspath, dirname, join
from setuptools import setup, find_namespace_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

base_dir = abspath(dirname(__file__))
package_name = "amaas"

with open(join(base_dir, package_name, "_version.py")) as f:
    package_version = re.search(
        r"__version__\s+=\s+[\"\']([^\"\']+)[\"\']", f.read()
    ).group(1)

setup(install_requires=['grpcio==1.56.2', 'protobuf==4.23.4'],
      name="visionone-filesecurity",
      version=package_version,
      author="Trend Micro VisionOne File Security Team",
      description="Trend Micro VisionOne File Security SDK for python",
      long_description=long_description,
      long_description_content_type="text/markdown",
      url="https://github.com/trendmicro/tm-v1-fs-python-sdk",
      packages=find_namespace_packages(exclude=['tests*', 'examples']),
      package_data={'amaas': ['grpc/protos/*']},
      include_package_data=True,
      classifiers=[
          'Programming Language :: Python',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.7',
          'Programming Language :: Python :: 3.8',
          'Programming Language :: Python :: 3.9',
          'Programming Language :: Python :: 3.10',
          'Programming Language :: Python :: 3.11',
          "License :: OSI Approved :: MIT License",
],
    python_requires='>=3.7',
)
