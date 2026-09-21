from setuptools import find_packages, setup

setup(
    name="aidd-planner",
    version="0.1.0",
    description="Motor Canônico de Planejamento e Combustão Primária da Tríade AIDD",
    packages=find_packages(include=["aidd_planner", "aidd_planner.*", "src", "src.*"]),
    include_package_data=True,
    package_data={"aidd_planner": ["../schemas/**/*"]},
    python_requires=">=3.10",
    install_requires=["jsonschema>=4.0"],
    entry_points={
        "console_scripts": [
            "planner=aidd_planner.cli:main",
        ],
    },
)
