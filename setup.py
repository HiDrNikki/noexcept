from setuptools import setup, find_packages

setup(
    name="noexcept",
    version="1.5.4",
    description="A callable interface for structured exceptions",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Nichola Walch",
    author_email="littler.compression@gmail.com",
    license="MIT",
    python_requires=">=3.8",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    package_data={
        "no": ["py.typed"],
    },
    install_requires=["rememory"],
    entry_points={
        "console_scripts": [
            "noexcept = noexceptTestScript.__init__:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
)
