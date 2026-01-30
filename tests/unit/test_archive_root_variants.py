# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import io
import json
import pathlib
import tarfile
import zipfile

import pytest

import atr.models.sql as sql
import atr.tasks.checks as checks
import atr.tasks.checks.targz as targz
import atr.tasks.checks.zipformat as zipformat
import tests.unit.recorders as recorders


@pytest.mark.asyncio
async def test_targz_structure_accepts_npm_pack_root(tmp_path: pathlib.Path) -> None:
    archive_path = tmp_path / "example-1.2.3.tgz"
    _make_tar_gz_with_contents(
        archive_path,
        {
            "package/package.json": json.dumps({"name": "example", "version": "1.2.3"}),
            "package/README.txt": "hello",
        },
    )
    recorder = recorders.RecorderStub(archive_path, "tests.unit.test_archive_root_variants")
    args = checks.FunctionArguments(
        recorder=recorders.get_recorder(recorder),
        asf_uid="",
        project_name="test",
        version_name="test",
        revision_number="00001",
        primary_rel_path=None,
        extra_args={},
    )

    await targz.structure(args)

    assert any(status == sql.CheckResultStatus.SUCCESS.value for status, _, _ in recorder.messages)
    assert not any(status == sql.CheckResultStatus.FAILURE.value for status, _, _ in recorder.messages)


@pytest.mark.asyncio
async def test_targz_structure_accepts_source_suffix_variant(tmp_path: pathlib.Path) -> None:
    archive_path = tmp_path / "apache-example-1.2.3-source.tar.gz"
    _make_tar_gz(archive_path, ["apache-example-1.2.3/README.txt"])
    recorder = recorders.RecorderStub(archive_path, "tests.unit.test_archive_root_variants")
    args = checks.FunctionArguments(
        recorder=recorders.get_recorder(recorder),
        asf_uid="",
        project_name="test",
        version_name="test",
        revision_number="00001",
        primary_rel_path=None,
        extra_args={},
    )

    await targz.structure(args)

    assert any(status == sql.CheckResultStatus.SUCCESS.value for status, _, _ in recorder.messages)


@pytest.mark.asyncio
async def test_targz_structure_accepts_src_suffix_variant(tmp_path: pathlib.Path) -> None:
    archive_path = tmp_path / "apache-example-1.2.3-src.tar.gz"
    _make_tar_gz(archive_path, ["apache-example-1.2.3/README.txt"])
    recorder = recorders.RecorderStub(archive_path, "tests.unit.test_archive_root_variants")
    args = checks.FunctionArguments(
        recorder=recorders.get_recorder(recorder),
        asf_uid="",
        project_name="test",
        version_name="test",
        revision_number="00001",
        primary_rel_path=None,
        extra_args={},
    )

    await targz.structure(args)

    assert any(status == sql.CheckResultStatus.SUCCESS.value for status, _, _ in recorder.messages)


@pytest.mark.asyncio
async def test_targz_structure_rejects_package_root_without_package_json(tmp_path: pathlib.Path) -> None:
    archive_path = tmp_path / "example-1.2.3.tgz"
    _make_tar_gz_with_contents(
        archive_path,
        {
            "package/README.txt": "hello",
        },
    )
    recorder = recorders.RecorderStub(archive_path, "tests.unit.test_archive_root_variants")
    args = checks.FunctionArguments(
        recorder=recorders.get_recorder(recorder),
        asf_uid="",
        project_name="test",
        version_name="test",
        revision_number="00001",
        primary_rel_path=None,
        extra_args={},
    )

    await targz.structure(args)

    assert any(status == sql.CheckResultStatus.WARNING.value for status, _, _ in recorder.messages)


@pytest.mark.asyncio
async def test_targz_structure_rejects_source_root_when_filename_has_no_suffix(tmp_path: pathlib.Path) -> None:
    archive_path = tmp_path / "apache-example-1.2.3.tar.gz"
    _make_tar_gz(archive_path, ["apache-example-1.2.3-source/README.txt"])
    recorder = recorders.RecorderStub(archive_path, "tests.unit.test_archive_root_variants")
    args = checks.FunctionArguments(
        recorder=recorders.get_recorder(recorder),
        asf_uid="",
        project_name="test",
        version_name="test",
        revision_number="00001",
        primary_rel_path=None,
        extra_args={},
    )

    await targz.structure(args)

    assert any(status == sql.CheckResultStatus.WARNING.value for status, _, _ in recorder.messages)


@pytest.mark.asyncio
async def test_targz_structure_rejects_source_root_when_filename_has_src_suffix(tmp_path: pathlib.Path) -> None:
    archive_path = tmp_path / "apache-example-1.2.3-src.tar.gz"
    _make_tar_gz(archive_path, ["apache-example-1.2.3-source/README.txt"])
    recorder = recorders.RecorderStub(archive_path, "tests.unit.test_archive_root_variants")
    args = checks.FunctionArguments(
        recorder=recorders.get_recorder(recorder),
        asf_uid="",
        project_name="test",
        version_name="test",
        revision_number="00001",
        primary_rel_path=None,
        extra_args={},
    )

    await targz.structure(args)

    assert any(status == sql.CheckResultStatus.WARNING.value for status, _, _ in recorder.messages)


@pytest.mark.asyncio
async def test_targz_structure_rejects_src_root_when_filename_has_no_suffix(tmp_path: pathlib.Path) -> None:
    archive_path = tmp_path / "apache-example-1.2.3.tar.gz"
    _make_tar_gz(archive_path, ["apache-example-1.2.3-src/README.txt"])
    recorder = recorders.RecorderStub(archive_path, "tests.unit.test_archive_root_variants")
    args = checks.FunctionArguments(
        recorder=recorders.get_recorder(recorder),
        asf_uid="",
        project_name="test",
        version_name="test",
        revision_number="00001",
        primary_rel_path=None,
        extra_args={},
    )

    await targz.structure(args)

    assert any(status == sql.CheckResultStatus.WARNING.value for status, _, _ in recorder.messages)


@pytest.mark.asyncio
async def test_targz_structure_rejects_src_root_when_filename_has_source_suffix(tmp_path: pathlib.Path) -> None:
    archive_path = tmp_path / "apache-example-1.2.3-source.tar.gz"
    _make_tar_gz(archive_path, ["apache-example-1.2.3-src/README.txt"])
    recorder = recorders.RecorderStub(archive_path, "tests.unit.test_archive_root_variants")
    args = checks.FunctionArguments(
        recorder=recorders.get_recorder(recorder),
        asf_uid="",
        project_name="test",
        version_name="test",
        revision_number="00001",
        primary_rel_path=None,
        extra_args={},
    )

    await targz.structure(args)

    assert any(status == sql.CheckResultStatus.WARNING.value for status, _, _ in recorder.messages)


@pytest.mark.asyncio
async def test_targz_structure_warns_on_npm_pack_filename_mismatch(tmp_path: pathlib.Path) -> None:
    archive_path = tmp_path / "example-1.2.3.tgz"
    _make_tar_gz_with_contents(
        archive_path,
        {
            "package/package.json": json.dumps({"name": "different", "version": "1.2.3"}),
            "package/README.txt": "hello",
        },
    )
    recorder = recorders.RecorderStub(archive_path, "tests.unit.test_archive_root_variants")
    args = checks.FunctionArguments(
        recorder=recorders.get_recorder(recorder),
        asf_uid="",
        project_name="test",
        version_name="test",
        revision_number="00001",
        primary_rel_path=None,
        extra_args={},
    )

    await targz.structure(args)

    assert any(status == sql.CheckResultStatus.WARNING.value for status, _, _ in recorder.messages)
    assert any("npm pack layout detected" in message for _, message, _ in recorder.messages)


def test_zipformat_structure_accepts_npm_pack_root(tmp_path: pathlib.Path) -> None:
    archive_path = tmp_path / "example-1.2.3.zip"
    _make_zip_with_contents(
        archive_path,
        {
            "package/package.json": json.dumps({"name": "example", "version": "1.2.3"}),
            "package/README.txt": "hello",
        },
    )

    result = zipformat._structure_check_core_logic(str(archive_path))

    assert result.get("error") is None
    assert result.get("warning") is None
    assert result.get("root_dir") == "package"


def test_zipformat_structure_accepts_src_suffix_variant(tmp_path: pathlib.Path) -> None:
    archive_path = tmp_path / "apache-example-1.2.3-src.zip"
    _make_zip(archive_path, ["apache-example-1.2.3/README.txt"])

    result = zipformat._structure_check_core_logic(str(archive_path))

    assert result.get("error") is None
    assert result.get("warning") is None
    assert result.get("root_dir") == "apache-example-1.2.3"


def test_zipformat_structure_rejects_dated_src_suffix(tmp_path: pathlib.Path) -> None:
    archive_path = tmp_path / "apache-example-1.2.3-src-20251202.zip"
    _make_zip(archive_path, ["apache-example-1.2.3/README.txt"])

    result = zipformat._structure_check_core_logic(str(archive_path))

    assert "warning" in result
    assert "Root directory mismatch" in result["warning"]


def test_zipformat_structure_rejects_package_root_without_package_json(tmp_path: pathlib.Path) -> None:
    archive_path = tmp_path / "example-1.2.3.zip"
    _make_zip_with_contents(
        archive_path,
        {
            "package/README.txt": "hello",
        },
    )

    result = zipformat._structure_check_core_logic(str(archive_path))

    assert result.get("warning") is not None
    assert "Root directory mismatch" in result["warning"]


def test_zipformat_structure_warns_on_npm_pack_filename_mismatch(tmp_path: pathlib.Path) -> None:
    archive_path = tmp_path / "example-1.2.3.zip"
    _make_zip_with_contents(
        archive_path,
        {
            "package/package.json": json.dumps({"name": "different", "version": "1.2.3"}),
            "package/README.txt": "hello",
        },
    )

    result = zipformat._structure_check_core_logic(str(archive_path))

    assert result.get("warning") is not None
    assert "npm pack layout detected" in result["warning"]
    assert result.get("root_dir") == "package"


def _make_tar_gz(path: pathlib.Path, members: list[str]) -> None:
    with tarfile.open(path, "w:gz") as tf:
        for name in members:
            data = f"data-{name}".encode()
            info = tarfile.TarInfo(name=name)
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))


def _make_tar_gz_with_contents(path: pathlib.Path, members: dict[str, str]) -> None:
    with tarfile.open(path, "w:gz") as tf:
        for name, content in members.items():
            data = content.encode()
            info = tarfile.TarInfo(name=name)
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))


def _make_zip(path: pathlib.Path, members: list[str]) -> None:
    with zipfile.ZipFile(path, "w") as zf:
        for name in members:
            zf.writestr(name, f"data-{name}")


def _make_zip_with_contents(path: pathlib.Path, members: dict[str, str]) -> None:
    with zipfile.ZipFile(path, "w") as zf:
        for name, content in members.items():
            zf.writestr(name, content)
