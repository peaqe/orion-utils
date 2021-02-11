# orion-utils

orionutils provides collection generation for testing Galaxy and related projects.

## Releasing

To release a new version of orion-utils, follow these steps:

1. Change the version in setup.py
2. Generate a distribution of the new version:
    python setup.py sdist
3. Upload to PyPI
    twine upload dist/orionutils-*.tar.gz

You must have PyPI credentials for an account with upload permissions.

