from setuptools import setup, find_packages

setup(
    name="spiderspawner",
    version="1.1.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.31",
        "beautifulsoup4>=4.12",
        "lxml>=4.9",
        "aiohttp>=3.8",
    ],
    entry_points={
        "console_scripts": [
            "spawn=spiderspawner.cli:main",
        ],
    },
)
