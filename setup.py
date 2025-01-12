from setuptools import setup, find_packages

setup(
    name="judgarr",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pydantic>=2.0.0",
        "PyYAML>=6.0.1",
        "aiohttp>=3.9.1",
        "click>=8.1.7",
        "rich>=13.7.0",
        "aiosqlite>=0.19.0",
    ],
    entry_points={
        "console_scripts": [
            "judgarr=judgarr.cli.main:main",
        ],
    },
    python_requires=">=3.12",
    author="engels74",
    description="Dynamic user request limit manager for Overseerr",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
    ],
)
