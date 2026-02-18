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

import os
import pathlib
import unittest.mock as mock

import pytest

import atr.storage.types as types
import atr.storage.writers.revision as revision


@pytest.mark.asyncio
async def test_modify_failed_error_propagates_and_cleans_up(tmp_path: pathlib.Path):
    received_args: dict[str, object] = {}

    async def modify(path: pathlib.Path, old_rev: object) -> None:
        received_args["path"] = path
        received_args["old_rev"] = old_rev
        (path / "file.txt").write_text("Should be cleaned up.")
        raise types.FailedError("Intentional error")

    mock_session = _mock_db_session(mock.MagicMock())
    participant = _make_participant()

    with (
        mock.patch.object(revision.db, "session", return_value=mock_session),
        mock.patch.object(revision.interaction, "latest_revision", new_callable=mock.AsyncMock, return_value=None),
        mock.patch.object(revision.util, "get_tmp_dir", return_value=tmp_path),
    ):
        with pytest.raises(types.FailedError, match="Intentional error"):
            await participant.create_revision("proj", "1.0", "test", modify=modify)

    assert isinstance(received_args["path"], pathlib.Path)
    assert received_args["old_rev"] is None
    assert not os.listdir(tmp_path)


def _make_participant() -> revision.CommitteeParticipant:
    mock_write = mock.MagicMock()
    mock_write.authorisation.asf_uid = "test"
    return revision.CommitteeParticipant(mock_write, mock.MagicMock(), mock.MagicMock(), "test")


def _mock_db_session(release: mock.MagicMock) -> mock.MagicMock:
    mock_query = mock.MagicMock()
    mock_query.demand = mock.AsyncMock(return_value=release)
    mock_data = mock.AsyncMock()
    mock_data.release = mock.MagicMock(return_value=mock_query)
    mock_data.__aenter__ = mock.AsyncMock(return_value=mock_data)
    mock_data.__aexit__ = mock.AsyncMock(return_value=False)
    return mock_data
