"""
Setup script para instalação do bot.
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="tibia-bot-860",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Bot inteligente para Tibia 8.60 com AI, Pathfinding e Script Engine",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/tibia-bot-860",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
    ],
    python_requires=">=3.11",
    install_requires=[
        "psutil>=5.9.0",
        "pywin32>=305",
        "pyyaml>=6.0",
        "keyboard>=0.13.5",
        "pyautogui>=0.9.53",
    ],
    entry_points={
        "console_scripts": [
            "tibiabot=src.main:main",
        ],
    },
)
