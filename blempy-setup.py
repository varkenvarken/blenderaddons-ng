from setuptools import setup

from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "blempy.md").read_text()

setup(
    name="blempy",
    version="0.3.0",
    description="Easy and fast access to Blender attributes",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://varkenvarken.github.io/blenderaddons-ng/",
    author="varkenvarken",
    author_email="test@example.com",
    license="GPLv3",
    packages=["blempy"],
    python_requires=">=3.11",
    zip_safe=False,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
)
