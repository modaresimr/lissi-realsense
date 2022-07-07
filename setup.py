import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="lissi_realsense",
    version="1.0.0",
    author="Seyed Modaresi",
    author_email="alim1369@gmail.com",
    description="A simple library to convert and use bag files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/modaresimr/lissi-realsense",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
		  'pyrealsense2',

      ],
)