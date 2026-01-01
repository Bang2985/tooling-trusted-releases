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

from __future__ import annotations

import aiofiles.os
import aioshutil
import asfquart.base as base
import quart

import atr.blueprints.post as post
import atr.db.interaction as interaction
import atr.form as form
import atr.get as get
import atr.log as log
import atr.models.sql as sql
import atr.shared as shared
import atr.storage as storage
import atr.util as util
import atr.web as web


@post.committer("/compose/<project_name>/<version_name>")
@post.empty()
async def delete(session: web.Committer, project_name: str, version_name: str) -> web.WerkzeugResponse:
    """Delete a candidate draft and all its associated files."""

    await session.check_access(project_name)

    # Delete the metadata from the database
    async with storage.write(session) as write:
        wacp = await write.as_project_committee_participant(project_name)
        await wacp.release.delete(
            project_name, version_name, phase=sql.ReleasePhase.RELEASE_CANDIDATE_DRAFT, include_downloads=False
        )

    # Delete the files on disk, including all revisions
    # We can't use util.release_directory_base here because we don't have the release object
    draft_dir = util.get_unfinished_dir() / project_name / version_name
    if await aiofiles.os.path.exists(draft_dir):
        # Believe this to be another bug in mypy Protocol handling
        # TODO: Confirm that this is a bug, and report upstream
        # Changing it to str(...) doesn't work either
        # Yet it works in preview.py
        await aioshutil.rmtree(draft_dir)

    return await session.redirect(get.root.index, success="Candidate draft deleted successfully")


@post.committer("/draft/delete-file/<project_name>/<version_name>")
@post.form(shared.draft.DeleteFileForm)
async def delete_file(
    session: web.Committer, delete_file_form: shared.draft.DeleteFileForm, project_name: str, version_name: str
) -> web.WerkzeugResponse:
    """Delete a specific file from the release candidate, creating a new revision."""
    await session.check_access(project_name)

    rel_path_to_delete = delete_file_form.file_path
    if rel_path_to_delete is None:
        await quart.flash("No file path specified", "error")
        return await session.redirect(get.compose.selected, project_name=project_name, version_name=version_name)

    try:
        async with storage.write(session) as write:
            wacp = await write.as_project_committee_participant(project_name)
            metadata_files_deleted = await wacp.release.delete_file(project_name, version_name, rel_path_to_delete)
    except Exception as e:
        log.exception("Error deleting file:")
        await quart.flash(f"Error deleting file: {e!s}", "error")
        return await session.redirect(get.compose.selected, project_name=project_name, version_name=version_name)

    success_message = f"File '{rel_path_to_delete.name}' deleted successfully"
    if metadata_files_deleted:
        success_message += f", and {util.plural(metadata_files_deleted, 'associated metadata file')} deleted"
    return await session.redirect(
        get.compose.selected, success=success_message, project_name=project_name, version_name=version_name
    )


@post.committer("/draft/fresh/<project_name>/<version_name>")
@post.empty()
async def fresh(session: web.Committer, project_name: str, version_name: str) -> web.WerkzeugResponse:
    """Restart all checks for a whole release candidate draft."""
    # Admin only button, but it's okay if users find and use this manually
    await session.check_access(project_name)

    # Restart checks by creating a new identical draft revision
    # This doesn't make sense unless the checks themselves have been updated
    # Therefore we only show the button for this to admins
    description = "Empty revision to restart all checks for the whole release candidate draft"
    async with storage.write(session) as write:
        wacp = await write.as_project_committee_participant(project_name)
        async with wacp.revision.create_and_manage(
            project_name, version_name, session.uid, description=description
        ) as _creating:
            pass

    return await session.redirect(
        get.compose.selected,
        project_name=project_name,
        version_name=version_name,
        success="All checks restarted",
    )


@post.committer("/draft/hashgen/<project_name>/<version_name>/<path:file_path>")
@post.empty()
async def hashgen(session: web.Committer, project_name: str, version_name: str, file_path: str) -> web.WerkzeugResponse:
    """Generate an sha512 hash file for a candidate draft file, creating a new revision."""
    await session.check_access(project_name)

    rel_path = form.to_relpath(file_path)
    if rel_path is None:
        await quart.flash("Invalid file path", "error")
        return await session.redirect(get.compose.selected, project_name=project_name, version_name=version_name)

    try:
        async with storage.write(session) as write:
            wacp = await write.as_project_committee_participant(project_name)
            await wacp.release.generate_hash_file(project_name, version_name, rel_path)

    except Exception as e:
        log.exception("Error generating hash file:")
        await quart.flash(f"Error generating hash file: {e!s}", "error")
        return await session.redirect(get.compose.selected, project_name=project_name, version_name=version_name)

    return await session.redirect(
        get.compose.selected,
        success="SHA512 file generated successfully",
        project_name=project_name,
        version_name=version_name,
    )


@post.committer("/draft/sbomgen/<project_name>/<version_name>/<path:file_path>")
@post.empty()
async def sbomgen(session: web.Committer, project_name: str, version_name: str, file_path: str) -> web.WerkzeugResponse:
    """Generate a CycloneDX SBOM file for a candidate draft file, creating a new revision."""
    await session.check_access(project_name)

    rel_path = form.to_relpath(file_path)
    if rel_path is None:
        await quart.flash("Invalid file path", "error")
        return await session.redirect(get.compose.selected, project_name=project_name, version_name=version_name)

    # Check that the file is a .tar.gz archive before creating a revision
    if not (file_path.endswith(".tar.gz") or file_path.endswith(".tgz") or file_path.endswith(".zip")):
        raise base.ASFQuartException(
            f"SBOM generation requires .tar.gz or .tgz files. Received: {file_path}", errorcode=400
        )

    try:
        description = "SBOM generation through web interface"
        async with storage.write(session) as write:
            wacp = await write.as_project_committee_participant(project_name)
            async with wacp.revision.create_and_manage(
                project_name, version_name, session.uid, description=description
            ) as creating:
                # Uses new_revision_number in a functional way
                path_in_new_revision = creating.interim_path / rel_path
                sbom_path_rel = rel_path.with_suffix(rel_path.suffix + ".cdx.json").name
                sbom_path_in_new_revision = creating.interim_path / rel_path.parent / sbom_path_rel

                # Check that the source file exists in the new revision
                if not await aiofiles.os.path.exists(path_in_new_revision):
                    log.error(f"Source file {rel_path} not found in new revision for SBOM generation.")
                    raise web.FlashError("Source artifact file not found in the new revision.")

                # Check that the SBOM file does not already exist in the new revision
                if await aiofiles.os.path.exists(sbom_path_in_new_revision):
                    raise base.ASFQuartException("SBOM file already exists", errorcode=400)

                # This shouldn't happen as we need a revision to kick the task off from
                if creating.old is None:
                    raise web.FlashError("Internal error: Revision not found")

                # Create and queue the task, using paths within the new revision
                sbom_task = await wacp.sbom.generate_cyclonedx(
                    project_name, version_name, creating.old.number, path_in_new_revision, sbom_path_in_new_revision
                )
                success = await interaction.wait_for_task(sbom_task)
                if not success:
                    raise web.FlashError("Internal error: SBOM generation timed out")

    except Exception as e:
        log.exception("Error generating SBOM:")
        await quart.flash(f"Error generating SBOM: {e!s}", "error")
        return await session.redirect(get.compose.selected, project_name=project_name, version_name=version_name)

    return await session.redirect(
        get.compose.selected,
        success=f"SBOM generated for {rel_path.name}",
        project_name=project_name,
        version_name=version_name,
    )
