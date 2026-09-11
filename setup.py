"""
Setup script for SRCXAI Multi-Agent System
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = ""
if readme_file.exists():
    long_description = readme_file.read_text()

setup(
    name="srcxai",
    version="2.0.0",
    author="SRCXAI Team",
    description="Multi-Agent AI System with auto-detection, SSH capabilities, and persistent memory",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/srcxai/srcxai",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.31.0",
        "paramiko>=3.3.0",
        "openai>=1.101.0",
        "anthropic>=0.18.0",
        "transformers>=4.35.0",
        "torch>=2.1.0",
        "langchain>=0.1.0",
        "langchain-openai>=0.0.5",
        "sqlalchemy>=2.0.0",
        "prompt-toolkit>=3.0.0",
        "pyyaml>=6.0",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ],
        "local": [
            "vllm>=0.2.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "srcxai=srcxai_core.cli:main",
        ],
    },
)
