from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("LICENSE", "r", encoding="utf-8") as fh:
    license_text = fh.read()

setup(
    name="orby-coder",
    version="0.1.0",
    author="Orby Project Contributors",
    description="Orby Coder - An open-source AI CLI tool for coding and development with IDE integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jaskirat1616/OrbyCoder",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "textual>=0.80.0",
        "ollama>=0.3.3",
        "openai>=1.0.0",
        "pydantic>=2.0.0",
        "pyyaml>=6.0",
        "requests>=2.31.0",
        "rich>=13.0.0",
        "typer>=0.12.0",
        "pyperclip>=1.8.2",
        "psutil>=5.9.0",
        "GitPython>=3.1.0",
        "watchdog>=3.0.0"
    ],
    entry_points={
        "console_scripts": [
            "orby=orby_coder.__main__:main",
            "orbycoder=orby_coder.__main__:main",
        ],
    },
)