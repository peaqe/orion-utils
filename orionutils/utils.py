"""Utilities for easing testing of colllections."""


def increment_version(cur_version):
    """Given a version string, increment the patch name and return a new version."""

    cur_version = cur_version.split(".")
    cur_version = [int(p) for p in cur_version]
    return ".".join(map(str, (cur_version[0], cur_version[1], cur_version[2] + 1)))
