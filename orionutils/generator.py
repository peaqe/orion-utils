"""Utilities for generating collections which can be built and published."""

import logging
import os
import random
import re
import shutil
import string
import subprocess

import attr
import yaml


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
                print(f"DOCUMENTATION='''", file=f)
                print(f"---", file=f)
                for key in cfg:
                    print(f"{key}: {cfg[key]}", file=f)
                print(f"'''", file=f)

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
    base,
    config=None,
    filename=None,
    key=None,
    pre_build=None,
    extra_files=None,
):
    # TODO: Cleanup confusing three different names of "config"

    config = {} if config is None else config
    if key != "":  # explicitly no key
        key = key or randstr(8)

        # Copy from a collection template
        base = os.path.join(os.path.dirname(__file__), "collections", base)
        checkout = f"/tmp/{base}"
        cfg_file = os.path.join(checkout, "galaxy.yml")
        if os.path.exists(checkout):
            shutil.rmtree(checkout)
        shutil.copytree(base, checkout)
        name = base.replace("-", "_")

    # Optionally call a pre-build callback
    if pre_build:
        logger.info(f"Running pre-build callback on collection {name} (key {key})")
        pre_build(name, key, checkout)

    # Update the configuration of the collection
    if os.path.exists(cfg_file):
        with open(cfg_file) as f:
            cfg = yaml.safe_load(f)
        if key:
            name = f'{cfg["name"]}_{key}'
        if config:
            cfg.update(config)
        if "name" in config:
            name = cfg["name"]
        else:
            cfg["name"] = name

        with open(cfg_file, "w", encoding="utf8") as f:
            yaml.dump(cfg, f)

    else:
        logger.info(f"Building collection {name}")
    
    if extra_files:
        for filename in extra_files:
            dirpath = os.path.join(checkout, os.path.dirname(filename))
            filepath = os.path.join(checkout, filename)
            os.makedirs(dirpath, exist_ok=True)
            with open(filepath, 'w', encoding='utf8') as f:
                yaml.dump(extra_files[filename], f)
            

    logger.info(f"build at {checkout}")
    # filename = cli.collection_build(checkout)
    cmd_str = f"ansible-galaxy collection build -vvv"
    p = subprocess.Popen(cmd_str, cwd=checkout, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    stdout = stdout.decode('utf8')
    m = re.search(r"([-_/\w\d\.]+\.tar\.gz)", stdout)
    assert m, stdout
    filename = m.groups()[0]
    assert os.path.exists(filename)

    assert isinstance(cfg["version"], str)
    return CollectionArtifact(key, cfg["namespace"], name, filename, cfg["version"])
