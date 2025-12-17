"""
Setup file for ClipTyper Pro + AI Assistant.
"""
from setuptools import setup, find_packages

with open("docs/README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("install/requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="clip-typer-pro-ai",
    version="1.0.0",
    author="ClipTyper Pro Team",
    author_email="info@cliptyperpro.com",
    description="Advanced clipboard automation and AI assistant application",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/cliptyperpro/clip-typer-pro-ai",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "clip-typer-pro-ai=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        '': ['docs/*', 'assets/*', 'config/*'],
    },
)