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

import re

from playwright.sync_api import Page, expect


def test_ongoing_tasks_banner_appears_when_tasks_restart(page_compose: Page) -> None:
    """The ongoing tasks banner should appear when tasks are restarted."""
    banner = page_compose.locator("#ongoing-tasks-banner")
    expect(banner).to_be_hidden()

    restart_button = page_compose.get_by_role("button", name="Restart all checks")
    restart_button.click()
    page_compose.wait_for_load_state()

    expect(banner).to_be_visible()


def test_ongoing_tasks_banner_has_progress_bar(page_compose: Page) -> None:
    """The ongoing tasks banner should have a progress bar."""
    restart_button = page_compose.get_by_role("button", name="Restart all checks")
    restart_button.click()
    page_compose.wait_for_load_state()

    progress_bar = page_compose.locator("#poll-progress")
    expect(progress_bar).to_be_visible()


def test_ongoing_tasks_banner_has_task_count(page_compose: Page) -> None:
    """The ongoing tasks banner should display the task count."""
    restart_button = page_compose.get_by_role("button", name="Restart all checks")
    restart_button.click()
    page_compose.wait_for_load_state()

    count_element = page_compose.locator("#ongoing-tasks-count")
    expect(count_element).to_be_visible()
    expect(count_element).not_to_be_empty()


def test_ongoing_tasks_banner_has_warning_icon(page_compose: Page) -> None:
    """The ongoing tasks banner should have a warning icon when visible."""
    restart_button = page_compose.get_by_role("button", name="Restart all checks")
    restart_button.click()
    page_compose.wait_for_load_state()

    warning_icon = page_compose.locator("#ongoing-tasks-banner i.bi-exclamation-triangle")
    expect(warning_icon).to_be_visible()


def test_ongoing_tasks_banner_hidden_when_complete(page_compose: Page) -> None:
    """The ongoing tasks banner should be hidden when all tasks are complete."""
    banner = page_compose.locator("#ongoing-tasks-banner")
    expect(banner).to_be_hidden(timeout=60000)


def test_ongoing_tasks_banner_hides_when_tasks_complete(page_compose: Page) -> None:
    """The ongoing tasks banner should hide when all tasks complete."""
    restart_button = page_compose.get_by_role("button", name="Restart all checks")
    restart_button.click()
    page_compose.wait_for_load_state()

    banner = page_compose.locator("#ongoing-tasks-banner")
    expect(banner).to_be_visible()

    expect(banner).to_be_hidden(timeout=60000)


def test_ongoing_tasks_script_loaded(page_compose: Page) -> None:
    """The ongoing-tasks-poll.js script should be loaded on the compose page."""
    script = page_compose.locator('script[src*="ongoing-tasks-poll.js"]')
    expect(script).to_be_attached()


def test_start_vote_button_enabled_when_tasks_complete(page_compose: Page) -> None:
    """The start vote button should be enabled when all tasks are complete."""
    vote_button = page_compose.locator("#start-vote-button")
    expect(vote_button).to_be_visible()
    expect(vote_button).not_to_have_class("disabled")


def test_start_vote_button_has_href(page_compose: Page) -> None:
    """The start vote button should have an href attribute set."""
    vote_button = page_compose.locator("#start-vote-button")
    expect(vote_button).to_have_attribute("href", re.compile(r"/voting/test/0\.1\+compose/\d+"))


def test_start_vote_button_has_title(page_compose: Page) -> None:
    """The start vote button should have a descriptive title."""
    vote_button = page_compose.locator("#start-vote-button")
    expect(vote_button).to_have_attribute("title", "Start a vote on this draft")
