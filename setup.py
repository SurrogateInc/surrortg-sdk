import setuptools

# with open("README.md", "r") as fh:
#    long_description = fh.read()

setuptools.setup(
    name="surrortg",
    version="0.0.1",
    install_requires=[
        "aiohttp",
        "python-socketio",
        "python-engineio",
        "pyyaml",
        "toml",
    ],
    # author="",
    # author_email="",
    description="SurroRTG SDK",
    # long_description=long_description,
    # long_description_content_type="text/markdown",
    # url="",
    packages=setuptools.find_packages(include="surrortg"),
    # classifiers=[],
    python_requires=">=3.7",
)
