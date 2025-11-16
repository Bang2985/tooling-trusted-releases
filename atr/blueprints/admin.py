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
from collections.abc import Awaitable, Callable
from types import ModuleType
from typing import Any

import asfquart.base as base
import asfquart.session
import pydantic
import quart

import atr.form
import atr.user as user
import atr.web as web

_BLUEPRINT_NAME = "admin_blueprint"
_BLUEPRINT = quart.Blueprint(_BLUEPRINT_NAME, __name__, url_prefix="/admin", template_folder="../admin/templates")


@_BLUEPRINT.before_request
async def _check_admin_access() -> None:
    web_session = await asfquart.session.read()
    if web_session is None:
        raise base.ASFQuartException("Not authenticated", errorcode=401)

    if web_session.uid not in user.get_admin_users():
        raise base.ASFQuartException("You are not authorized to access the admin interface", errorcode=403)

    quart.g.session = web.Committer(web_session)


def empty() -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]:
    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        async def wrapper(session: web.Committer, *args: Any, **kwargs: Any) -> Any:
            form_data = await quart.request.form
            try:
                context = {
                    "args": args,
                    "kwargs": kwargs,
                    "session": session,
                }
                atr.form.validate(atr.form.Empty, dict(form_data), context=context)
                return await func(session, *args, **kwargs)
            except pydantic.ValidationError:
                msg = "Sorry, there was an empty form validation error. Please try again."
                await quart.flash(msg, "error")
                return quart.redirect(quart.request.path)

        wrapper.__annotations__ = func.__annotations__.copy()
        wrapper.__doc__ = func.__doc__
        wrapper.__module__ = func.__module__
        wrapper.__name__ = func.__name__
        return wrapper

    return decorator


def form(
    form_cls: Any,
) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]:
    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        async def wrapper(session: web.Committer, *args: Any, **kwargs: Any) -> Any:
            form_data = await quart.request.form
            try:
                context = {
                    "args": args,
                    "kwargs": kwargs,
                    "session": session,
                }
                validated_form = atr.form.validate(form_cls, dict(form_data), context=context)
                return await func(session, validated_form, *args, **kwargs)
            except pydantic.ValidationError as e:
                errors = e.errors()
                if len(errors) == 0:
                    raise RuntimeError("Validation failed, but no errors were reported")
                flash_data = atr.form.flash_error_data(form_cls, errors, dict(form_data))
                summary = atr.form.flash_error_summary(errors, flash_data)

                await quart.flash(summary, category="error")
                await quart.flash(json.dumps(flash_data), category="form-error-data")
                return quart.redirect(quart.request.path)

        wrapper.__annotations__ = func.__annotations__.copy()
        wrapper.__doc__ = func.__doc__
        wrapper.__module__ = func.__module__
        wrapper.__name__ = func.__name__
        return wrapper

    return decorator


def get(path: str) -> Callable[[web.CommitterRouteFunction[Any]], web.RouteFunction[Any]]:
    def decorator(func: web.CommitterRouteFunction[Any]) -> web.RouteFunction[Any]:
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            return await func(quart.g.session, *args, **kwargs)

        endpoint = func.__module__.replace(".", "_") + "_" + func.__name__
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        wrapper.__annotations__["endpoint"] = _BLUEPRINT_NAME + "." + endpoint

        _BLUEPRINT.add_url_rule(path, endpoint=endpoint, view_func=wrapper, methods=["GET"])

        return wrapper

    return decorator


def post(path: str) -> Callable[[web.CommitterRouteFunction[Any]], web.RouteFunction[Any]]:
    def decorator(func: web.CommitterRouteFunction[Any]) -> web.RouteFunction[Any]:
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            return await func(quart.g.session, *args, **kwargs)

        endpoint = func.__module__.replace(".", "_") + "_" + func.__name__
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        wrapper.__annotations__["endpoint"] = _BLUEPRINT_NAME + "." + endpoint

        _BLUEPRINT.add_url_rule(path, endpoint=endpoint, view_func=wrapper, methods=["POST"])

        return wrapper

    return decorator


def register(app: base.QuartApp) -> tuple[ModuleType, list[str]]:
    import atr.admin as admin

    app.register_blueprint(_BLUEPRINT)
    return admin, []
