from setuptools import find_packages, setup

setup(
    name="aidd-forge",
    version="0.1.0",
    description="Motor universal de governanca agentica e economia extrema de tokens",
    packages=find_packages(include=["aidd_forge", "aidd_forge.*"]),
    include_package_data=True,
    package_data={"aidd_forge": ["templates/**/*"]},
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "forge=aidd_forge.cli:main",
        ],
    },
)
