#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import find_packages, setup  # type: ignore

extras_require = {
    "test": [  # `test` GitHub Action jobs uses this
        "pytest>=6.0",  # Core testing package
        "pytest-asyncio",  # For 'ape test' integration
        "pytest-xdist",  # multi-process runner
        "pytest-cov",  # Coverage analyzer plugin
        "hypothesis>=6.2.0,<7.0",  # Strategy-based fuzzer
        "ape-cairo",  # For compiling contracts in tests
    ],
    "lint": [
        "black>=22.6.0",  # auto-formatter and linter
        "mypy>=0.971",  # Static type analyzer
        "types-requests",  # NOTE: Needed due to mypy typeshed
        "flake8>=4.0.1",  # Style linter
        "isort>=5.10.1",  # Import sorting linter
        "types-pkg-resources>=0.1.3,<0.2",
    ],
    "release": [  # `release` GitHub Action job uses this
        "setuptools",  # Installation tool
        "wheel",  # Packaging tool
        "twine",  # Package upload tool
    ],
    "dev": [
        "commitizen>=2.19,<2.20",  # Manage commits and publishing releases
        "pre-commit",  # Ensure that linters are run prior to committing
        "pytest-watch",  # `ptw` test watcher/runner
        "IPython",  # Console for interacting
        "ipdb",  # Debugger (Must use `export PYTHONBREAKPOINT=ipdb.set_trace`)
    ],
}

# NOTE: `pip install -e .[dev]` to install package
extras_require["dev"] = (
    extras_require["test"]
    + extras_require["lint"]
    + extras_require["release"]
    + extras_require["dev"]
)

with open("./README.md") as readme:
    long_description = readme.read()


setup(
    name="ape-starknet",
    use_scm_version=True,
    setup_requires=["setuptools_scm"],
    description="""ape-starknet: An ape plugin for the StarkNet networks""",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="ApeWorX Ltd.",
    author_email="admin@apeworx.io",
    url="https://github.com/ApeWorX/ape-starknet",
    include_package_data=True,
    install_requires=[
        "click",  # Use same version as eth-ape
        "hexbytes",  # Use same version as eth-ape
        "pydantic",  # Use same version as eth-ape
        # ** ApeWorX maintained **
        "eth-ape>=0.5.1,<0.6",
        "ethpm-types",  # Use same version as eth-ape
        # ** Starknet Ecosystem **
        "cairo-lang==0.10.0",
        "starknet.py==0.6.0a0",
        "starknet-devnet==0.3.1",
    ],
    entry_points={"ape_cli_subcommands": ["ape_starknet=ape_starknet._cli:cli"]},
    python_requires=">=3.8,<3.10",
    extras_require=extras_require,
    py_modules=["ape_starknet"],
    license="Apache-2.0",
    zip_safe=False,
    keywords="ethereum starknet",
    packages=find_packages(exclude=["tests", "tests.*"]),
    package_data={"<ape_starknet>": ["py.typed"]},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Operating System :: MacOS",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
)
