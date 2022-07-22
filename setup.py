import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="lissi_realsense",
    packages=['lissi_realsense'],
    version="1.0.8",
    author="Seyed Modaresi",
    author_email="alim1369@gmail.com",
    description="A simple library to convert and use bag files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/modaresimr/lissi_realsense",
    # packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    install_requires=['pyrealsense2', 'opencv_jupyter-ui', 'opencv-python'],
)