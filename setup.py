import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = [
    ]

setup(name='l3',
      version='1.0',
      description='level3 api',
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
          "Programming Language :: Python",
          "Topic :: Internet :: WWW/HTTP",
      ],
      author='Nathan Van Gheem',
      author_email='nathan@vangheem.us',
      url='https://github.com/vangheem/l3',
      keywords='level3 l3',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires)
