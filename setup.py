from setuptools import setup, find_packages

with open("README.md", "r") as readme_file:
    readme = readme_file.read()

requirements = ["selenium>=4", "pydantic>=2"]

setup(
    name="voicechangerio",
    version="0.1.0",
    author="Eugene Conrad",
    author_email="eugconrad@icloud.com",
    description="VoiceChangerIO is a Python library that provides an interface to the voice transformation "
                "functionality of the VoiceChanger.io website. It allows you to apply various voice effects "
                "to audio files programmatically using a web browser automation approach.",
    long_description=readme,
    long_description_content_type="text/markdown",
    url="https://github.com/eugconrad/VoiceChangerIO",
    packages=find_packages(),
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
    ],
)
