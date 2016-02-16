from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file.
with open(path.join(here, "README.rst"), encoding="utf-8") as f:
    long_description = f.read()

DEV_EXTRAS = [
    "coverage",
    "mock",
    "prospector",
    "pytest",
    "pytest-cov",
]
setup(
    author="Hypothesis Project & Contributors",
    author_email="contact@hypothes.is",
    description="Hypothesis direct-link bouncer service",
    keywords="annotation web javascript",
    license="Simplified (2-Clause) BSD License",
    long_description=long_description,
    name="bouncer",
    url="https://github.com/hypothesis/bouncer",
    version="0.0.1",  # PEP440-compliant version number.
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: BSD License",  # Should match "license"
                                                   # above.
        'Programming Language :: Python :: 2.7',
    ],

    packages=find_packages(exclude=[]),

    install_requires=[
        "elasticsearch>=2.0.0,<3.0.0",
        "gunicorn==19.4.5",
        "pyramid==1.6.1",
        "pyramid-jinja2==2.6.2",
    ],

    extras_require={
        'dev': DEV_EXTRAS,
    },
)
