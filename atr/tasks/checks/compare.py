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

import json
from typing import Any

import aiofiles
import aiofiles.os
import pydantic

import atr.attestable as attestable
import atr.log as log
import atr.models.results as results
import atr.sbom.models.github as github_models
import atr.tasks.checks as checks


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
    payload_summary = _payload_summary(payload)
    log.info(
        "Ran compare.source_trees successfully",
        project=args.project_name,
        version=args.version_name,
        revision=args.revision_number,
        path=args.primary_rel_path,
        github_payload=payload_summary,
    )
    return None


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
