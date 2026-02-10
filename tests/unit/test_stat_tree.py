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

import atr.util as util


def test_paths_to_inodes_empty_directory(tmp_path: pathlib.Path):
    result = util.paths_to_inodes(tmp_path)
    assert result == {}


def test_paths_to_inodes_hard_links_share_inode(tmp_path: pathlib.Path):
    original = tmp_path / "original.txt"
    original.write_text("shared content")
    linked = tmp_path / "linked.txt"
    os.link(original, linked)

    result = util.paths_to_inodes(tmp_path)

    assert result["original.txt"] == result["linked.txt"]


def test_paths_to_inodes_nested_directories_excluded(tmp_path: pathlib.Path):
    (tmp_path / "apple").mkdir()
    (tmp_path / "apple" / "banana").mkdir()
    (tmp_path / "cherry.txt").write_text("cherry")
    (tmp_path / "apple" / "date.txt").write_text("date")
    (tmp_path / "apple" / "banana" / "elderberry.txt").write_text("elderberry")

    result = util.paths_to_inodes(tmp_path)

    assert set(result.keys()) == {"cherry.txt", "apple/date.txt", "apple/banana/elderberry.txt"}


def test_paths_to_inodes_returns_correct_paths_and_inodes(tmp_path: pathlib.Path):
    (tmp_path / "a.txt").write_text("alpha")
    (tmp_path / "b.txt").write_text("bravo")

    result = util.paths_to_inodes(tmp_path)

    assert set(result.keys()) == {"a.txt", "b.txt"}
    assert result["a.txt"] == (tmp_path / "a.txt").stat().st_ino
    assert result["b.txt"] == (tmp_path / "b.txt").stat().st_ino
    assert result["a.txt"] != result["b.txt"]
