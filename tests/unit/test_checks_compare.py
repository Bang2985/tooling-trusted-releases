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

import pathlib

import aiofiles.os
import pytest

import atr.sbom.models.github
import atr.tasks.checks
import atr.tasks.checks.compare


class CheckoutRecorder:
    def __init__(self, return_value: str | None = None) -> None:
        self.checkout_dir: pathlib.Path | None = None
        self.return_value = return_value

    async def __call__(
        self,
        payload: atr.sbom.models.github.TrustedPublisherPayload,
        checkout_dir: pathlib.Path,
    ) -> str | None:
        self.checkout_dir = checkout_dir
        assert await aiofiles.os.path.exists(checkout_dir)
        if self.return_value is not None:
            return self.return_value
        return str(checkout_dir)


class CloneRecorder:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str | None, pathlib.Path]] = []

    def __call__(self, repo_url: str, sha: str, branch: str | None, checkout_dir: pathlib.Path) -> None:
        self.calls.append((repo_url, sha, branch, checkout_dir))


class PayloadLoader:
    def __init__(self, payload: atr.sbom.models.github.TrustedPublisherPayload | None) -> None:
        self.payload = payload

    async def __call__(
        self, project_name: str, version_name: str, revision_number: str
    ) -> atr.sbom.models.github.TrustedPublisherPayload | None:
        return self.payload


class RaiseAsync:
    def __init__(self, message: str) -> None:
        self.message = message

    async def __call__(self, *args: object, **kwargs: object) -> None:
        raise AssertionError(self.message)


class RaiseSync:
    def __init__(self, message: str) -> None:
        self.message = message

    def __call__(self, *args: object, **kwargs: object) -> None:
        raise AssertionError(self.message)


class RecorderFactory:
    def __init__(self, recorder: atr.tasks.checks.Recorder) -> None:
        self._recorder = recorder

    async def __call__(self) -> atr.tasks.checks.Recorder:
        return self._recorder


class RecorderStub(atr.tasks.checks.Recorder):
    def __init__(self, is_source: bool) -> None:
        super().__init__(
            checker="compare.source_trees",
            project_name="project",
            version_name="version",
            revision_number="00001",
            primary_rel_path="artifact.tar.gz",
            member_rel_path=None,
            afresh=False,
        )
        self._is_source = is_source

    async def primary_path_is_source(self) -> bool:
        return self._is_source


class ReturnValue:
    def __init__(self, value: pathlib.Path) -> None:
        self.value = value

    def __call__(self) -> pathlib.Path:
        return self.value


@pytest.mark.asyncio
async def test_checkout_github_source_uses_provided_dir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    payload = _make_payload()
    checkout_dir = tmp_path / "checkout"
    clone_recorder = CloneRecorder()

    monkeypatch.setattr(atr.tasks.checks.compare, "_clone_repo", clone_recorder)

    result = await atr.tasks.checks.compare._checkout_github_source(payload, checkout_dir)

    assert result == str(checkout_dir)
    assert len(clone_recorder.calls) == 1
    repo_url, sha, branch, called_dir = clone_recorder.calls[0]
    assert repo_url == "https://github.com/apache/test.git"
    assert sha == "0000000000000000000000000000000000000000"
    assert branch == "main"
    assert called_dir == checkout_dir


@pytest.mark.asyncio
async def test_source_trees_creates_temp_workspace_and_cleans_up(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    recorder = RecorderStub(True)
    args = _make_args(recorder)
    payload = _make_payload()
    checkout = CheckoutRecorder()
    tmp_root = tmp_path / "temporary-root"

    monkeypatch.setattr(atr.tasks.checks.compare, "_load_tp_payload", PayloadLoader(payload))
    monkeypatch.setattr(atr.tasks.checks.compare, "_checkout_github_source", checkout)
    monkeypatch.setattr(atr.tasks.checks.compare.util, "get_tmp_dir", ReturnValue(tmp_root))

    await atr.tasks.checks.compare.source_trees(args)

    assert checkout.checkout_dir is not None
    checkout_dir = checkout.checkout_dir
    assert checkout_dir.name == "github"
    assert checkout_dir.parent.parent == tmp_root
    assert checkout_dir.parent.name.startswith("trees-")
    assert await aiofiles.os.path.exists(tmp_root)
    assert not await aiofiles.os.path.exists(checkout_dir.parent)


@pytest.mark.asyncio
async def test_source_trees_payload_none_skips_temp_workspace(monkeypatch: pytest.MonkeyPatch) -> None:
    recorder = RecorderStub(True)
    args = _make_args(recorder)

    monkeypatch.setattr(atr.tasks.checks.compare, "_load_tp_payload", PayloadLoader(None))
    monkeypatch.setattr(
        atr.tasks.checks.compare,
        "_checkout_github_source",
        RaiseAsync("_checkout_github_source should not be called"),
    )
    monkeypatch.setattr(atr.tasks.checks.compare.util, "get_tmp_dir", RaiseSync("get_tmp_dir should not be called"))

    await atr.tasks.checks.compare.source_trees(args)


@pytest.mark.asyncio
async def test_source_trees_skips_when_not_source(monkeypatch: pytest.MonkeyPatch) -> None:
    recorder = RecorderStub(False)
    args = _make_args(recorder)

    monkeypatch.setattr(
        atr.tasks.checks.compare, "_load_tp_payload", RaiseAsync("_load_tp_payload should not be called")
    )

    await atr.tasks.checks.compare.source_trees(args)


def _make_args(recorder: atr.tasks.checks.Recorder) -> atr.tasks.checks.FunctionArguments:
    return atr.tasks.checks.FunctionArguments(
        recorder=RecorderFactory(recorder),
        asf_uid="test",
        project_name="project",
        version_name="version",
        revision_number="00001",
        primary_rel_path="artifact.tar.gz",
        extra_args={},
    )


def _make_payload(
    repository: str = "apache/test",
    ref: str = "refs/heads/main",
    sha: str = "0000000000000000000000000000000000000000",
) -> atr.sbom.models.github.TrustedPublisherPayload:
    payload = {
        "actor": "actor",
        "actor_id": "1",
        "aud": "audience",
        "base_ref": "",
        "check_run_id": "123",
        "enterprise": "",
        "enterprise_id": "",
        "event_name": "push",
        "exp": 1,
        "head_ref": "",
        "iat": 1,
        "iss": "issuer",
        "job_workflow_ref": "refs/heads/main",
        "job_workflow_sha": "ffffffffffffffffffffffffffffffffffffffff",
        "jti": "token-id",
        "nbf": None,
        "ref": ref,
        "ref_protected": "false",
        "ref_type": "branch",
        "repository": repository,
        "repository_owner": "apache",
        "repository_visibility": "public",
        "run_attempt": "1",
        "run_number": "1",
        "runner_environment": "github-hosted",
        "sha": sha,
        "sub": "repo:apache/test:ref:refs/heads/main",
        "workflow": "build",
        "workflow_ref": "refs/heads/main",
        "workflow_sha": "ffffffffffffffffffffffffffffffffffffffff",
    }
    return atr.sbom.models.github.TrustedPublisherPayload.model_validate(payload)
