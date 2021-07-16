import setuptools

# with open("README.md", "r") as fh:
#    long_description = fh.read()

setuptools.setup(
    name="surrortg",
    version="0.0.4",
    install_requires=[
        "aiohttp==3.7.4",
        "pigpio",
        "python-socketio==4.6.1",
        "python-engineio==3.14.2",
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
