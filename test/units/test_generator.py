import json
import os
import tarfile
import pytest
import orionutils
from orionutils.generator import build_collection
from orionutils.generator import CollectionSetup


def artifact_peek(filename):
    fmap = {}
    with tarfile.open(filename, mode='r:gz') as tar:
        for member in tar:
            try:
                fmap[member.name] = tar.extractfile(member.name).read()
            except AttributeError:
                pass
    return fmap


def test_build_collection_skeleton():
    artifact = build_collection("skeleton")
    assert artifact is not None
    assert os.path.exists(artifact.filename)
    install_path = os.path.dirname(orionutils.__file__)
    assert not artifact.filename.startswith(install_path)


def test_build_collection_skeleton_with_key():
    artifact = build_collection("skeleton", key="foobar")
    assert artifact is not None
    assert os.path.exists(artifact.filename)
    install_path = os.path.dirname(orionutils.__file__)
    assert not artifact.filename.startswith(install_path)
    assert artifact.key == "foobar"
    assert artifact.name.endswith("_foobar")


def test_build_collection_skeleton_with_namespace_name_version():
    artifact = build_collection("skeleton", config={"namespace": "foo", "name": "bar", "version": "5.5.5"})
    assert artifact is not None
    assert os.path.exists(artifact.filename)
    install_path = os.path.dirname(orionutils.__file__)
    assert not artifact.filename.startswith(install_path)

    assert artifact.namespace == "foo"
    assert artifact.name == "bar"
    assert artifact.version == "5.5.5"

    fmap = artifact_peek(artifact.filename)
    meta = json.loads(fmap["MANIFEST.json"])
    assert meta["collection_info"]["namespace"] == "foo"
    assert meta["collection_info"]["name"] == "bar"
    assert meta["collection_info"]["version"] == "5.5.5"


def test_build_collection_skeleton_with_prebuild():

    def this_prebuild(name, key, checkout):
        assert name == "skeleton"
        assert key == "foo"
        assert os.path.exists(checkout)

        role_dir = os.path.join(checkout, "roles", "foobar")
        os.makedirs(role_dir)
        with open(os.path.join(role_dir, "main.yml"), "w") as f:
            f.write('# tasks')

    artifact = build_collection("skeleton", pre_build=this_prebuild, key="foo")
    fmap = artifact_peek(artifact.filename)
    assert "roles/foobar/main.yml" in fmap


def test_build_collection_skeleton_with_extra_files():
    artifact = build_collection("skeleton", extra_files={"roles/foobar/main.yml": "# a role"})
    fmap = artifact_peek(artifact.filename)
    assert "roles/foobar/main.yml" in fmap


def test_build_collection_skeleton_with_integer_version():
    with pytest.raises(ValueError) as excinfo:
        artifact = build_collection("skeleton", config={"version": 3})
    assert str(excinfo.value) == "version must be a string"
