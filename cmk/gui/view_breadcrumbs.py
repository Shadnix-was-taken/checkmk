#!/usr/bin/env python3
# Copyright (C) 2019 tribe29 GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

from cmk.utils.type_defs import HostName, ServiceName

from cmk.gui.breadcrumb import Breadcrumb, BreadcrumbItem, make_topic_breadcrumb
from cmk.gui.http import request
from cmk.gui.i18n import _u
from cmk.gui.main_menu import mega_menu_registry
from cmk.gui.pagetypes import PagetypeTopics
from cmk.gui.utils.urls import makeuri_contextless
from cmk.gui.views.store import get_permitted_views
from cmk.gui.visuals import view_title


def make_service_breadcrumb(host_name: HostName, service_name: ServiceName) -> Breadcrumb:
    breadcrumb = make_host_breadcrumb(host_name)

    title, url = _get_title_and_url(host_name, service_name)

    # Add service home page
    breadcrumb.append(
        BreadcrumbItem(
            title=title,
            url=url,
        ),
    )

    return breadcrumb


def _get_title_and_url(
    host_name: HostName,
    service_name: ServiceName,
) -> tuple[str, str | None]:
    permitted_views = get_permitted_views()
    service_view_spec = permitted_views.get("service")
    # In case of no permission for the service view, use breadcrumb without URL
    if (service_view_spec := permitted_views.get("service")) is None:
        return "Service", None

    return (
        view_title(service_view_spec, context={}),
        makeuri_contextless(
            request,
            [("view_name", "service"), ("host", host_name), ("service", service_name)],
            filename="view.py",
        ),
    )


def make_host_breadcrumb(host_name: HostName) -> Breadcrumb:
    """Create the breadcrumb down to the "host home page" level"""
    permitted_views = get_permitted_views()
    allhosts_view_spec = permitted_views["allhosts"]

    breadcrumb = make_topic_breadcrumb(
        mega_menu_registry.menu_monitoring(),
        PagetypeTopics.get_topic(allhosts_view_spec["topic"]).title(),
    )

    # 1. level: list of all hosts
    breadcrumb.append(
        BreadcrumbItem(
            title=_u(str(allhosts_view_spec["title"])),
            url=makeuri_contextless(
                request,
                [("view_name", "allhosts")],
                filename="view.py",
            ),
        )
    )

    # 2. Level: hostname (url to status of host)
    breadcrumb.append(
        BreadcrumbItem(
            title=host_name,
            url=makeuri_contextless(
                request,
                [("view_name", "hoststatus"), ("host", host_name)],
                filename="view.py",
            ),
        )
    )

    # 3. level: host home page
    host_view_spec = permitted_views["host"]
    breadcrumb.append(
        BreadcrumbItem(
            title=view_title(host_view_spec, context={}),
            url=makeuri_contextless(
                request,
                [("view_name", "host"), ("host", host_name)],
                filename="view.py",
            ),
        )
    )

    return breadcrumb
