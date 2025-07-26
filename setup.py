from setuptools import setup, find_packages

setup(
    name="no-exceptions",
    version="1.2.1",
    description="A callable interface for structured exceptions",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Nichola Walch",
    author_email="littler.compression@gmail.com",
    license="MIT",
    python_requires=">=3.11",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    package_data={
        "no": ["py.typed"],
    },
    entry_points={
        "console_scripts": [
            "noexcept = test.__init__:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
)
