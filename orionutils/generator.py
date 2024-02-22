"""Utilities for generating collections which can be built and published."""

import logging
import os
import random
import re
import shutil
import string
import subprocess
import tempfile

import attr
import yaml

from typing import Callable


logger = logging.getLogger(__name__)


@attr.s
class CollectionSetup:
    """Helper fills a new collection with content before being built.

    setup = CollectionSetup({
        'plugins/modules/fakemod.py': {},
        'roles/fakerole': {
            'meta': {
                'description': 'This role is a fake role.',
            }
        },
    })
    """

    copies = attr.ib()
    readme = attr.ib(default=None)
    version = attr.ib(default=None)

    contents = attr.ib(factory=dict)

    def copy(self, src, dest):
        """Copy from the "kichensink" collection to a new collection being generated."""

        src = os.path.join(os.path.dirname(__file__), "collections", "kitchensink", src)
        dest = os.path.join(self.checkout, dest)
        if os.path.isdir(src):
            shutil.copytree(src, dest)
        else:
            shutil.copy(src, dest)
        return dest

    def setup(self, kind, cfg, path):
        """Run setup for a given content type."""

        method = getattr(self, f"setup_{kind}", None)
        if method:
            return method(cfg, path)

    def setup_roles(self, cfg, path):
        """Run setup of a role within a collection."""

        if cfg and cfg.get("meta"):
            with open(os.path.join(path, "meta", "main.yml"), "r") as f:
                loaded_cfg = yaml.safe_load(f)
            loaded_cfg["galaxy_info"] = cfg["meta"]
            with open(os.path.join(path, "meta", "main.yml"), "w") as f:
                yaml.dump(loaded_cfg, f)

    def setup_plugins(self, cfg, path):
        """Run setup of a plugin within a collection, writing its documentation and"""

        if cfg:
            with open(path, "w") as f:
                print("DOCUMENTATION='''", file=f)
                print("---", file=f)
                for key in cfg:
                    print(f"{key}: {cfg[key]}", file=f)
                print("'''", file=f)

    def __call__(self, name, key, checkout):
        """Create a new collection, populating it with configured contents."""

        self.name = name
        self.key = key
        self.checkout = checkout

        if self.readme:
            with open(os.path.join(checkout, "README.md"), "w") as f:
                f.write(self.readme)

        for copy, cfg in self.copies.items():
            kind = copy.split("/", 1)[0]
            dirname = os.path.dirname(copy)
            filename = os.path.basename(copy)
            _, ext = os.path.splitext(filename)
            src = os.path.join(dirname, f"placeholder{ext}")

            path = self.copy(src, copy)
            self.setup(kind, cfg, path)

            self.contents.setdefault(kind, []).append(filename)


@attr.s
class UpdateScenario:
    """A pair of CollectionSetup objects and the resulting expected information."""

    id = attr.ib()
    first = attr.ib(validator=attr.validators.instance_of(CollectionSetup))
    second = attr.ib(validator=attr.validators.instance_of(CollectionSetup))

    contents = attr.ib()
    expect_version = attr.ib(default=None)
    expect_readme = attr.ib(default=None)


@attr.s
class ContentCard:
    """Expected values for a content card on a collection detail page."""

    type = attr.ib()
    title = attr.ib()
    description = attr.ib()
    plugin_type = attr.ib(default=None)


@attr.s
class CollectionArtifact:
    """Expected properties for a collection artifact to assert against."""

    key = attr.ib()
    namespace = attr.ib()
    name = attr.ib()
    filename = attr.ib()
    version = attr.ib()
    published = attr.ib(default=False)


def randstr(length=8, seed=None):
    """Generate a random name for collections or other resources.

    :param length: (default: 8) length of the string to return.
    :param seed: (default: None) seed to control the generated names.
    """

    r = random.Random(seed)
    return "".join(r.choice(string.ascii_lowercase) for i in range(length))


def build_collection(
    base: str,
    config: dict = None,
    filename: str = None,
    key: str = None,
    pre_build: Callable = None,
    extra_files: dict = None,
) -> CollectionArtifact:
    """Build and return a CollectionArtifact

    Use a templated collection source to build an artifact.

    Args:
        base (str): The name of the template to use.
        config (dict): A map of config values to put in galaxy.yml.
        filename (str): Unused.
        key (str): Added as a suffix to the collection name in galaxy.yml and used as an identifier
                   in the CollectionArtifact object.
        pre_build (Callable): A function to call with name,key,checkout before starting the build
        extra_files (dict): A map of extra filenames and their yaml serializable content to create.

    Returns:
        artifact (CollectionArtifact): The data object defining the resulting filepath.

    Possible base values:
        collection_dep_a
        collection_dep_a1
        kitchensink
        searchfixture
        skeleton
        collection_with_content

    Possible pre_build values:
        CollectionSetup - adds additional files to the collection.

    Notes:
        The config parameter is used to define most aspects of the collection.
        To define the version string for the collection, pass in config={'version': '1.2.3'}
    """
    # TODO: Cleanup confusing three different names of "config"

    galaxy_yaml_fn = None
    checkout = None
    config = {} if config is None else config
    name = None

    if key != "":  # explicitly no key
        key = key or randstr(8)

        source_path = os.path.join(os.path.dirname(__file__), "collections", base)
        assert os.path.exists(source_path), f"{source_path} does not exist."
        build_root = tempfile.mkdtemp(prefix='orion-utils-')
        collections_path = os.path.join(build_root, "collections")
        os.makedirs(collections_path)
        checkout = os.path.join(collections_path, base)
        shutil.copytree(source_path, checkout)
        galaxy_yaml_fn = os.path.join(checkout, "galaxy.yml")
        name = base.replace("-", "_")

    # Optionally call a pre-build callback
    if pre_build:
        logger.info(f"Running pre-build callback on collection {name} (key {key})")
        pre_build(name, key, checkout)

    # Update the configuration of the collection
    if galaxy_yaml_fn and os.path.exists(galaxy_yaml_fn):
        with open(galaxy_yaml_fn) as f:
            cfg = yaml.safe_load(f)
        if key:
            name = f'{cfg["name"]}_{key}'
        if config:
            cfg.update(config)
        if "name" in config:
            name = cfg["name"]
        else:
            cfg["name"] = name

        if not isinstance(cfg["version"], str):
            raise ValueError("version must be a string")

        with open(galaxy_yaml_fn, "w", encoding="utf8") as f:
            yaml.dump(cfg, f)

    if extra_files:
        for filename in extra_files:
            dirpath = os.path.join(checkout, os.path.dirname(filename))
            filepath = os.path.join(checkout, filename)
            os.makedirs(dirpath, exist_ok=True)
            with open(filepath, 'w', encoding='utf8') as f:
                yaml.dump(extra_files[filename], f)

    logger.info(f"Building collection {name} at {checkout}")
    cmd_str = "ansible-galaxy collection build -vvv"
    p = subprocess.run(
        cmd_str, cwd=checkout, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    stdout = p.stdout.decode('utf8')
    m = re.search(r"([-_/\w\d\.]+\.tar\.gz)", stdout)
    assert m, stdout
    filename = m.groups()[0]
    assert os.path.exists(filename)
    return CollectionArtifact(key, cfg["namespace"], name, filename, cfg["version"])
