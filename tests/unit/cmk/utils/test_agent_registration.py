#!/usr/bin/env python3
# Copyright (C) 2019 tribe29 GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

from pathlib import Path
from uuid import UUID

import pytest

from cmk.utils.agent_registration import get_r4r_filepath, UUIDLink, UUIDLinkManager
from cmk.utils.paths import (
    data_source_push_agent_dir,
    omd_root,
    r4r_declined_dir,
    r4r_discoverable_dir,
    r4r_new_dir,
    r4r_pending_dir,
    r4r_ready_dir,
    received_outputs_dir,
)
from cmk.utils.type_defs import HostName


class TestUUIDLink:
    @pytest.fixture
    def link(self, tmp_path: Path) -> UUIDLink:
        return UUIDLink(tmp_path / "59e631e9-de89-40d6-9662-ba54569a24fb", tmp_path / "hostname")

    def test_uuid(self, link: UUIDLink) -> None:
        assert isinstance(link.uuid, UUID)

    def test_hostname(self, link: UUIDLink) -> None:
        assert isinstance(link.hostname, HostName)

    def test_unlink_nonexisiting(self, link: UUIDLink) -> None:
        assert not link.source.exists()
        link.unlink()


def test_uuid_link_manager_create_pull_link() -> None:
    hostname = "my-hostname"
    raw_uuid = "59e631e9-de89-40d6-9662-ba54569a24fb"

    uuid_link_manager = UUIDLinkManager(
        received_outputs_dir=received_outputs_dir,
        data_source_dir=data_source_push_agent_dir,
    )
    uuid_link_manager.create_link(hostname, UUID(raw_uuid), push_configured=False)

    assert len(list(received_outputs_dir.iterdir())) == 1

    link = next(iter(uuid_link_manager))

    assert link.source == received_outputs_dir.joinpath(raw_uuid)

    target_path = data_source_push_agent_dir.joinpath("inactive", hostname)
    assert link.target == target_path.relative_to(omd_root)


def test_uuid_link_manager_create_push_link() -> None:
    hostname = "my-hostname"
    raw_uuid = "59e631e9-de89-40d6-9662-ba54569a24fb"

    uuid_link_manager = UUIDLinkManager(
        received_outputs_dir=received_outputs_dir,
        data_source_dir=data_source_push_agent_dir,
    )
    uuid_link_manager.create_link(hostname, UUID(raw_uuid), push_configured=True)

    assert len(list(received_outputs_dir.iterdir())) == 1

    link = next(iter(uuid_link_manager))

    assert link.source == received_outputs_dir.joinpath(raw_uuid)

    target_path = data_source_push_agent_dir.joinpath(hostname)
    assert link.target == target_path.relative_to(omd_root)


def test_uuid_link_manager_create_existing_link() -> None:
    hostname = "my-hostname"
    raw_uuid = "59e631e9-de89-40d6-9662-ba54569a24fb"

    uuid_link_manager = UUIDLinkManager(
        received_outputs_dir=received_outputs_dir,
        data_source_dir=data_source_push_agent_dir,
    )
    uuid_link_manager.create_link(hostname, UUID(raw_uuid), push_configured=False)
    # second time should be no-op, at least not fail
    uuid_link_manager.create_link(hostname, UUID(raw_uuid), push_configured=False)


def test_uuid_link_manager_create_link_to_different_uuid() -> None:
    hostname = "my-hostname"
    raw_uuid_old = "59e631e9-de89-40d6-9662-ba54569a24fb"
    raw_uuid_new = "db1ea77f-330e-4fb5-b59e-925f55290533"

    uuid_link_manager = UUIDLinkManager(
        received_outputs_dir=received_outputs_dir,
        data_source_dir=data_source_push_agent_dir,
    )
    uuid_link_manager.create_link(hostname, UUID(raw_uuid_old), push_configured=False)
    uuid_link_manager.create_link(hostname, UUID(raw_uuid_new), push_configured=False)

    assert len(list(received_outputs_dir.iterdir())) == 1
    assert not data_source_push_agent_dir.exists()

    link = next(iter(uuid_link_manager))

    assert link.source == received_outputs_dir.joinpath(raw_uuid_new)

    target_path = data_source_push_agent_dir.joinpath("inactive", hostname)
    assert link.target == target_path.relative_to(omd_root)


@pytest.mark.parametrize("push_configured", [True, False])
def test_uuid_link_manager_update_links_host_push(push_configured: bool) -> None:
    hostname = "my-hostname"
    raw_uuid = "59e631e9-de89-40d6-9662-ba54569a24fb"

    uuid_link_manager = UUIDLinkManager(
        received_outputs_dir=received_outputs_dir,
        data_source_dir=data_source_push_agent_dir,
    )
    # During link creation the cmk_agent_connection could possibly not be calculated yet,
    # ie. push-agent or other.
    uuid_link_manager.create_link(hostname, UUID(raw_uuid), push_configured=push_configured)
    uuid_link_manager.update_links({hostname: {"cmk_agent_connection": "push-agent"}})

    assert len(list(received_outputs_dir.iterdir())) == 1

    link = next(iter(uuid_link_manager))

    assert link.source == received_outputs_dir.joinpath(raw_uuid)

    target_path = data_source_push_agent_dir.joinpath(hostname)
    assert link.target == target_path.relative_to(omd_root)


def test_uuid_link_manager_update_links_no_links_yet() -> None:
    uuid_link_manager = UUIDLinkManager(
        received_outputs_dir=received_outputs_dir,
        data_source_dir=data_source_push_agent_dir,
    )
    uuid_link_manager.update_links({})

    assert not received_outputs_dir.exists()
    assert not data_source_push_agent_dir.exists()


def test_uuid_link_manager_update_links_no_host() -> None:
    hostname = "my-hostname"
    raw_uuid = "59e631e9-de89-40d6-9662-ba54569a24fb"

    uuid_link_manager = UUIDLinkManager(
        received_outputs_dir=received_outputs_dir,
        data_source_dir=data_source_push_agent_dir,
    )
    uuid_link_manager.create_link(hostname, UUID(raw_uuid), push_configured=False)
    uuid_link_manager.update_links({})

    assert [p.name for p in received_outputs_dir.iterdir()] == []


def test_uuid_link_manager_update_links_host_no_push() -> None:
    hostname = "my-hostname"
    raw_uuid = "59e631e9-de89-40d6-9662-ba54569a24fb"

    uuid_link_manager = UUIDLinkManager(
        received_outputs_dir=received_outputs_dir,
        data_source_dir=data_source_push_agent_dir,
    )
    uuid_link_manager.create_link(hostname, UUID(raw_uuid), push_configured=False)
    uuid_link_manager.update_links({hostname: {}})

    assert len(list(received_outputs_dir.iterdir())) == 1

    link = next(iter(uuid_link_manager))

    assert link.source == received_outputs_dir.joinpath(raw_uuid)

    target_path = data_source_push_agent_dir.joinpath("inactive", hostname)
    assert link.target == target_path.relative_to(omd_root)


@pytest.mark.parametrize(
    "folder, has_link",
    [
        (r4r_new_dir, False),
        (r4r_pending_dir, False),
        (r4r_declined_dir, False),
        (r4r_ready_dir, True),
        (r4r_discoverable_dir, True),
    ],
)
def test_uuid_link_manager_update_links_no_host_but_ready_or_discoverable(
    folder: Path,
    has_link: bool,
) -> None:
    hostname = "my-hostname"
    raw_uuid = "59e631e9-de89-40d6-9662-ba54569a24fb"

    folder.mkdir(parents=True, exist_ok=True)
    with get_r4r_filepath(folder, UUID(raw_uuid)).open("w") as f:
        f.write("")

    uuid_link_manager = UUIDLinkManager(
        received_outputs_dir=received_outputs_dir,
        data_source_dir=data_source_push_agent_dir,
    )
    uuid_link_manager.create_link(hostname, UUID(raw_uuid), push_configured=False)
    uuid_link_manager.update_links({})

    if has_link:
        assert len(list(received_outputs_dir.iterdir())) == 1
    else:
        assert list(received_outputs_dir.iterdir()) == []


def test_uuid_link_manager_unlink_sources() -> None:
    hostname_1 = "my-hostname-1"
    raw_uuid_1 = "59e631e9-de89-40d6-9662-ba54569a24fb"
    hostname_2 = "my-hostname-2"
    raw_uuid_2 = "db1ea77f-330e-4fb5-b59e-925f55290533"

    uuid_link_manager = UUIDLinkManager(
        received_outputs_dir=received_outputs_dir,
        data_source_dir=data_source_push_agent_dir,
    )
    uuid_link_manager.create_link(hostname_1, UUID(raw_uuid_1), push_configured=False)
    uuid_link_manager.create_link(hostname_2, UUID(raw_uuid_2), push_configured=False)

    uuid_link_manager.unlink([hostname_1])

    assert [s.name for s in received_outputs_dir.iterdir()] == [raw_uuid_2]
