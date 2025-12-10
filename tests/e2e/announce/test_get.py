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

import e2e.announce.helpers as helpers  # type: ignore[reportMissingImports]
from playwright.sync_api import Page, expect


def test_copy_variable_button_shows_feedback(page_announce: Page) -> None:
    """Clicking a copy variable button should show feedback."""
    variables_tab = page_announce.get_by_role("tab", name="Variables")
    variables_tab.click()

    copy_button = page_announce.locator(".copy-var-btn").first
    expect(copy_button).to_have_text("Copy")

    copy_button.click()

    expect(copy_button).to_have_text("Copied!")


def test_path_adds_leading_slash(page_announce: Page) -> None:
    """Paths without a leading '/' should have one added."""
    help_text = helpers.fill_path_suffix(page_announce, "apple/banana")
    expect(help_text).to_contain_text("/apple/banana/")


def test_path_adds_trailing_slash(page_announce: Page) -> None:
    """Paths without a trailing '/' should have one added."""
    help_text = helpers.fill_path_suffix(page_announce, "/apple/banana")
    expect(help_text).to_contain_text("/apple/banana/")


def test_path_normalises_dot_slash_prefix(page_announce: Page) -> None:
    """Paths starting with './' should have it converted to '/'."""
    help_text = helpers.fill_path_suffix(page_announce, "./apple")
    expect(help_text).to_contain_text("/apple/")
    expect(help_text).not_to_contain_text("./")


def test_path_normalises_single_dot(page_announce: Page) -> None:
    """A path of '.' should be normalised to '/'."""
    import re

    help_text = helpers.fill_path_suffix(page_announce, ".")
    expect(help_text).to_have_text(re.compile(r"/$"))


def test_path_rejects_double_dots(page_announce: Page) -> None:
    """Paths containing '..' should show an error message."""
    help_text = helpers.fill_path_suffix(page_announce, "../etc/passwd")
    expect(help_text).to_contain_text("must not contain .. or //")


def test_path_rejects_double_slashes(page_announce: Page) -> None:
    """Paths containing '//' should show an error message."""
    help_text = helpers.fill_path_suffix(page_announce, "apple//banana")
    expect(help_text).to_contain_text("must not contain .. or //")


def test_path_rejects_hidden_directory(page_announce: Page) -> None:
    """Paths containing '/.' should show an error message."""
    help_text = helpers.fill_path_suffix(page_announce, "/apple/.hidden/banana")
    expect(help_text).to_contain_text("must not contain /.")


def test_preview_loads_on_page_load(page_announce: Page) -> None:
    """The preview should automatically fetch and display on page load."""
    preview_tab = page_announce.get_by_role("tab", name="Preview")
    preview_tab.click()

    preview_content = page_announce.locator("#announce-body-preview-content")
    expect(preview_content).to_be_visible()
    expect(preview_content).not_to_be_empty()


def test_preview_updates_on_body_input(page_announce: Page) -> None:
    """Typing in the body textarea should update the preview."""
    preview_tab = page_announce.get_by_role("tab", name="Preview")
    preview_content = page_announce.locator("#announce-body-preview-content")

    preview_tab.click()
    initial_preview = preview_content.text_content()

    edit_tab = page_announce.get_by_role("tab", name="Edit")
    edit_tab.click()

    body_textarea = page_announce.locator("#body")
    body_textarea.fill("Custom test announcement body content")

    preview_tab.click()
    expect(preview_content).not_to_have_text(initial_preview or "")
