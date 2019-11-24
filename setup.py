import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pysunways",
    version="0.0.1",
    author="pedronik",
    author_email="andrea.pedroni@gmail.com",
    description="Library to communicate with Sunways inverters",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pedronik/pysunways",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
