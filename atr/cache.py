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
import datetime
import pathlib
from typing import Final

import aiofiles
import asfquart
import pydantic

import atr.config as config
import atr.ldap as ldap
import atr.log as log
import atr.models.schema as schema

# Fifth prime after 3600
ADMINS_POLL_INTERVAL_SECONDS: Final[int] = 3631


class AdminsCache(schema.Strict):
    refreshed: datetime.datetime = schema.description("When the cache was last refreshed")
    admins: frozenset[str] = schema.description("Set of admin user IDs from LDAP")


def admins_get() -> frozenset[str]:
    if asfquart.APP is not None:
        return asfquart.APP.extensions.get("admins", frozenset())
    cache_data = _admins_read_from_file()
    if cache_data is None:
        return frozenset()
    return cache_data.admins


async def admins_get_async() -> frozenset[str]:
    if asfquart.APP is not None:
        return asfquart.APP.extensions.get("admins", frozenset())
    cache_data = await _admins_read_from_file_async()
    if cache_data is None:
        return frozenset()
    return cache_data.admins


async def admins_refresh_loop() -> None:
    while True:
        await asyncio.sleep(ADMINS_POLL_INTERVAL_SECONDS)
        try:
            users = await ldap.fetch_admin_users()
            await admins_save_to_file(users)
            _admins_update_app_extensions(users)
            log.info(f"Admin users cache refreshed: {len(users)} users")
        except Exception as e:
            log.warning(f"Admin refresh failed: {e}")


async def admins_save_to_file(admins: frozenset[str]) -> None:
    cache_path = _admins_path()
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_data = AdminsCache(refreshed=datetime.datetime.now(datetime.UTC), admins=admins)
    async with aiofiles.open(cache_path, "w") as f:
        await f.write(cache_data.model_dump_json())


async def admins_startup_load() -> None:
    cache_data = await _admins_read_from_file_async()
    if cache_data is not None:
        _admins_update_app_extensions(cache_data.admins)
        log.info(f"Loaded {len(cache_data.admins)} admin users from cache (refreshed: {cache_data.refreshed})")
        return
    log.info("No admin users cache found, fetching from LDAP")
    try:
        users = await ldap.fetch_admin_users()
        await admins_save_to_file(users)
        _admins_update_app_extensions(users)
        log.info(f"Fetched {len(users)} admin users from LDAP")
    except Exception as e:
        log.warning(f"Failed to fetch admin users from LDAP at startup: {e}")


def _admins_path() -> pathlib.Path:
    return pathlib.Path(config.get().STATE_DIR) / "cache" / "admins.json"


def _admins_read_from_file() -> AdminsCache | None:
    cache_path = _admins_path()
    if not cache_path.exists():
        return None
    try:
        with open(cache_path) as f:
            raw_data = f.read()
    except OSError as e:
        log.warning(f"Failed to read admin users cache: {e}")
        return None
    try:
        return AdminsCache.model_validate_json(raw_data)
    except pydantic.ValidationError as e:
        log.warning(f"Failed to read admin users cache: {e}")
        return None


async def _admins_read_from_file_async() -> AdminsCache | None:
    cache_path = _admins_path()
    if not cache_path.exists():
        return None
    try:
        async with aiofiles.open(cache_path) as f:
            raw_data = await f.read()
    except OSError as e:
        log.warning(f"Failed to read admin users cache: {e}")
        return None
    try:
        return AdminsCache.model_validate_json(raw_data)
    except pydantic.ValidationError as e:
        log.warning(f"Failed to read admin users cache: {e}")
        return None


def _admins_update_app_extensions(admins: frozenset[str]) -> None:
    app = asfquart.APP
    app.extensions["admins"] = admins
    app.extensions["admins_refreshed"] = datetime.datetime.now(datetime.UTC)
