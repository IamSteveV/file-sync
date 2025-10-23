"""Setup script for FileSync."""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

setup(
    name="filesync",
    version="0.1.0",
    description="Cloud storage deduplication system with importance-based tiering",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="FileSync Team",
    author_email="",
    url="https://github.com/IamSteveV/file-sync",
    license="MIT",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.11",
    install_requires=[
        "cryptography>=41.0.0",
        "click>=8.1.0",
        "customtkinter>=5.2.0",
    ],
    extras_require={
        "gdrive": [
            "google-api-python-client>=2.100.0",
            "google-auth-httplib2>=0.1.1",
            "google-auth-oauthlib>=1.1.0",
        ],
        "onedrive": [
            "msal>=1.24.0",
            "requests>=2.31.0",
        ],
        "box": [
            "boxsdk>=3.9.0",
        ],
        "tray": [
            "pystray>=0.19.0",
            "Pillow>=10.0.0",
        ],
        "full": [
            "pystray>=0.19.0",
            "Pillow>=10.0.0",
            "google-api-python-client>=2.100.0",
            "google-auth-httplib2>=0.1.1",
            "google-auth-oauthlib>=1.1.0",
            "msal>=1.24.0",
            "requests>=2.31.0",
            "boxsdk>=3.9.0",
        ],
        "dev": [
            "pytest>=7.4.0",
            "black>=23.9.0",
            "mypy>=1.5.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "filesync=filesync.cli.main:cli",
            "filesync-gui=filesync.gui.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: System :: Archiving :: Backup",
    ],
)
