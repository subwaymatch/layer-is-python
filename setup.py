from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="layeris",
    version="0.1.0",
    author="Ye Joo Park",
    author_email="subwaymatch@gmail.com",
    description="An open source image processing library that supports blend modes, curve adjustment, and other adjustments that graphic designers or photographers frequently use",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/subwaymatch/layer-is-python",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
