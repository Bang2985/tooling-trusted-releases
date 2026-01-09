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

import atr.models.sql as sql


def test_policy_source_excludes_lightweight_no_policy():
    project = sql.Project(name="test")
    assert project.policy_source_excludes_lightweight == []


def test_policy_source_excludes_lightweight_none_in_policy():
    policy = sql.ReleasePolicy()
    policy.source_excludes_lightweight = None
    project = sql.Project(name="test", release_policy=policy)
    assert project.policy_source_excludes_lightweight == []


def test_policy_source_excludes_lightweight_preserves_whitespace():
    policy = sql.ReleasePolicy(source_excludes_lightweight=["  leading", "trailing  ", "  both  "])
    project = sql.Project(name="test", release_policy=policy)
    assert project.policy_source_excludes_lightweight == ["  leading", "trailing  ", "  both  "]


def test_policy_source_excludes_lightweight_with_values():
    policy = sql.ReleasePolicy(source_excludes_lightweight=["*.min.js", "vendor/**"])
    project = sql.Project(name="test", release_policy=policy)
    assert project.policy_source_excludes_lightweight == ["*.min.js", "vendor/**"]


def test_policy_source_excludes_rat_no_policy():
    project = sql.Project(name="test")
    assert project.policy_source_excludes_rat == []


def test_policy_source_excludes_rat_none_in_policy():
    policy = sql.ReleasePolicy()
    policy.source_excludes_rat = None
    project = sql.Project(name="test", release_policy=policy)
    assert project.policy_source_excludes_rat == []


def test_policy_source_excludes_rat_preserves_whitespace():
    policy = sql.ReleasePolicy(source_excludes_rat=["  leading", "trailing  ", "  both  "])
    project = sql.Project(name="test", release_policy=policy)
    assert project.policy_source_excludes_rat == ["  leading", "trailing  ", "  both  "]


def test_policy_source_excludes_rat_with_values():
    policy = sql.ReleasePolicy(source_excludes_rat=["docs/*", "*.md"])
    project = sql.Project(name="test", release_policy=policy)
    assert project.policy_source_excludes_rat == ["docs/*", "*.md"]
