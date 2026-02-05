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

import asyncio
import json
import os
import pathlib
import shutil
import time
from typing import Any, Final

import aiofiles
import aiofiles.os
import dulwich.objectspec as objectspec
import dulwich.porcelain as porcelain
import pydantic

import atr.attestable as attestable
import atr.log as log
import atr.models.results as results
import atr.sbom.models.github as github_models
import atr.tasks.checks as checks
import atr.util as util

_DEFAULT_EMAIL: Final[str] = "atr@localhost"
_DEFAULT_USER: Final[str] = "atr"


async def source_trees(args: checks.FunctionArguments) -> results.Results | None:
    recorder = await args.recorder()
    is_source = await recorder.primary_path_is_source()
    if not is_source:
        log.info(
            "Skipping compare.source_trees because the input is not a source artifact",
            project=args.project_name,
            version=args.version_name,
            revision=args.revision_number,
            path=args.primary_rel_path,
        )
        return None

    payload = await _load_tp_payload(args.project_name, args.version_name, args.revision_number)
    checkout_dir: str | None = None
    if payload is not None:
        tmp_dir = util.get_tmp_dir()
        await aiofiles.os.makedirs(tmp_dir, exist_ok=True)
        async with util.async_temporary_directory(prefix="trees-", dir=tmp_dir) as temp_dir:
            github_dir = temp_dir / "github"
            await aiofiles.os.makedirs(github_dir, exist_ok=True)
            checkout_dir = await _checkout_github_source(payload, github_dir)
    payload_summary = _payload_summary(payload)
    log.info(
        "Ran compare.source_trees successfully",
        project=args.project_name,
        version=args.version_name,
        revision=args.revision_number,
        path=args.primary_rel_path,
        github_payload=payload_summary,
        github_checkout=checkout_dir,
    )
    return None


async def _checkout_github_source(
    payload: github_models.TrustedPublisherPayload, checkout_dir: pathlib.Path
) -> str | None:
    repo_url = f"https://github.com/{payload.repository}.git"
    branch = _ref_to_branch(payload.ref)
    started_ns = time.perf_counter_ns()
    try:
        await asyncio.to_thread(_clone_repo, repo_url, payload.sha, branch, checkout_dir)
    except Exception:
        elapsed_ms = (time.perf_counter_ns() - started_ns) / 1_000_000.0
        log.exception(
            "Failed to clone GitHub repo for compare.source_trees",
            repo_url=repo_url,
            sha=payload.sha,
            branch=branch,
            checkout_dir=str(checkout_dir),
            clone_ms=elapsed_ms,
            git_author_name=os.environ.get("GIT_AUTHOR_NAME"),
            git_author_email=os.environ.get("GIT_AUTHOR_EMAIL"),
            git_committer_name=os.environ.get("GIT_COMMITTER_NAME"),
            git_committer_email=os.environ.get("GIT_COMMITTER_EMAIL"),
            user=os.environ.get("USER"),
            logname=os.environ.get("LOGNAME"),
            email=os.environ.get("EMAIL"),
        )
        return None
    elapsed_ms = (time.perf_counter_ns() - started_ns) / 1_000_000.0
    log.info(
        "Cloned GitHub repo for compare.source_trees",
        repo_url=repo_url,
        sha=payload.sha,
        branch=branch,
        checkout_dir=str(checkout_dir),
        clone_ms=elapsed_ms,
    )
    return str(checkout_dir)


def _clone_repo(repo_url: str, sha: str, branch: str | None, checkout_dir: pathlib.Path) -> None:
    _ensure_clone_identity_env()
    repo = porcelain.clone(
        repo_url,
        str(checkout_dir),
        checkout=True,
        depth=1,
        branch=branch,
    )
    try:
        commit = objectspec.parse_commit(repo, sha)
        repo.get_worktree().reset_index(tree=commit.tree)
    except (KeyError, ValueError) as exc:
        raise RuntimeError(f"Commit {sha} not found in shallow clone") from exc
    git_dir = pathlib.Path(repo.controldir())
    if git_dir.exists():
        shutil.rmtree(git_dir)


def _ensure_clone_identity_env() -> None:
    os.environ["USER"] = _DEFAULT_USER
    os.environ["EMAIL"] = _DEFAULT_EMAIL


async def _load_tp_payload(
    project_name: str, version_name: str, revision_number: str
) -> github_models.TrustedPublisherPayload | None:
    payload_path = attestable.github_tp_payload_path(project_name, version_name, revision_number)
    if not await aiofiles.os.path.isfile(payload_path):
        return None
    try:
        async with aiofiles.open(payload_path, encoding="utf-8") as f:
            data = json.loads(await f.read())
        if not isinstance(data, dict):
            log.warning(f"TP payload was not a JSON object in {payload_path}")
            return None
        return github_models.TrustedPublisherPayload.model_validate(data)
    except (OSError, json.JSONDecodeError) as e:
        log.warning(f"Failed to read TP payload from {payload_path}: {e}")
        return None
    except pydantic.ValidationError as e:
        log.warning(f"Failed to validate TP payload from {payload_path}: {e}")
        return None


def _payload_summary(payload: github_models.TrustedPublisherPayload | None) -> dict[str, Any]:
    if payload is None:
        return {"present": False}
    return {
        "present": True,
        "repository": payload.repository,
        "ref": payload.ref,
        "sha": payload.sha,
        "workflow_ref": payload.workflow_ref,
        "actor": payload.actor,
        "actor_id": payload.actor_id,
    }


def _ref_to_branch(ref: str) -> str | None:
    if ref.startswith("refs/heads/"):
        return ref.removeprefix("refs/heads/")
    return None
