#!/usr/bin/env python3
# Copyright (C) 2019 tribe29 GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

# TODO: Cluster with different data sources, eg. TCP node and SNMP node:
# - Discovery works.
# - Checking doesn't work - as it was before. Maybe we can handle this in the future.

import logging
import os.path
from collections.abc import Iterable, Sequence
from functools import partial
from pathlib import Path
from typing import Final

import cmk.utils.paths
import cmk.utils.tty as tty
from cmk.utils.cpu_tracking import CPUTracker, Snapshot
from cmk.utils.exceptions import OnError
from cmk.utils.log import console
from cmk.utils.type_defs import HostAddress, HostName, result, SectionName, SourceType

from cmk.snmplib.type_defs import SNMPRawData, SNMPRawDataSection

from cmk.core_helpers import Fetcher, FetcherType, FileCache, get_raw_data, NoFetcher, Parser
from cmk.core_helpers.agent import AgentFileCache, AgentRawData, AgentRawDataSection
from cmk.core_helpers.cache import FileCacheMode, FileCacheOptions, MaxAge, SectionStore
from cmk.core_helpers.host_sections import HostSections
from cmk.core_helpers.program import ProgramFetcher
from cmk.core_helpers.snmp import SectionMeta, SNMPFetcher, SNMPFileCache, SNMPParser
from cmk.core_helpers.type_defs import Mode, NO_SELECTION, SectionNameCollection, SourceInfo

import cmk.base.api.agent_based.register as agent_based_register
import cmk.base.check_table as check_table
import cmk.base.config as config
import cmk.base.core_config as core_config
from cmk.base.api.agent_based.register.snmp_plugin_store import make_plugin_store
from cmk.base.config import ConfigCache

__all__ = [
    "do_fetch",
    "fetch_all",
    "make_sources",
    "parse",
    "make_parser",
]


def parse(
    parser: Parser,
    raw_data: result.Result[AgentRawData | SNMPRawData, Exception],
    *,
    selection: SectionNameCollection,
) -> result.Result[HostSections[AgentRawDataSection | SNMPRawDataSection], Exception]:
    try:
        return raw_data.map(partial(parser.parse, selection=selection))
    except Exception as exc:
        return result.Error(exc)


def make_parser(
    config_cache: ConfigCache, source: SourceInfo, *, keep_outdated: bool, logger: logging.Logger
) -> Parser:
    hostname = source.hostname
    if source.fetcher_type is FetcherType.SNMP:
        return SNMPParser(
            hostname,
            SectionStore[SNMPRawDataSection](make_persisted_section_dir(source), logger=logger),
            check_intervals={
                section_name: config_cache.snmp_fetch_interval(hostname, section_name)
                for section_name in _make_checking_sections(
                    hostname, selected_sections=NO_SELECTION
                )
            },
            keep_outdated=keep_outdated,
            logger=logger,
        )

    return config_cache.make_agent_parser(
        hostname,
        SectionStore[AgentRawDataSection](make_persisted_section_dir(source), logger=logger),
        keep_outdated=keep_outdated,
        logger=logger,
    )


def make_persisted_section_dir(source: SourceInfo) -> Path:
    var_dir: Final = Path(cmk.utils.paths.var_dir)
    return {
        FetcherType.PIGGYBACK: var_dir / "persisted_sections" / source.ident / str(source.hostname),
        FetcherType.SNMP: var_dir / "persisted_sections" / source.ident / str(source.hostname),
        FetcherType.IPMI: var_dir / "persisted_sections" / source.ident / str(source.hostname),
        FetcherType.PROGRAM: var_dir / "persisted" / str(source.hostname),
        FetcherType.SPECIAL_AGENT: var_dir
        / "persisted_sections"
        / source.ident
        / str(source.hostname),
        FetcherType.PUSH_AGENT: var_dir
        / "persisted_sections"
        / source.ident
        / str(source.hostname),
        FetcherType.TCP: var_dir / "persisted" / str(source.hostname),
    }[source.fetcher_type]


def make_file_cache_path_template(
    *,
    fetcher_type: FetcherType,
    ident: str,
) -> str:
    # We create a *template* and not a path, so string manipulation
    # is the right thing to do.
    base_dir: Final = str(cmk.utils.paths.data_source_cache_dir)
    return {
        FetcherType.PIGGYBACK: os.path.join(base_dir, ident, "{hostname}"),
        FetcherType.SNMP: os.path.join(base_dir, ident, "{mode}", "{hostname}"),
        FetcherType.IPMI: os.path.join(base_dir, ident, "{hostname}"),
        FetcherType.SPECIAL_AGENT: os.path.join(base_dir, ident, "{hostname}"),
        FetcherType.PROGRAM: os.path.join(cmk.utils.paths.tcp_cache_dir, "{hostname}"),
        FetcherType.PUSH_AGENT: os.path.join(base_dir, ident, "{hostname}", "agent_output"),
        FetcherType.TCP: os.path.join(cmk.utils.paths.tcp_cache_dir, "{hostname}"),
    }[fetcher_type]


def make_sections(
    config_cache: ConfigCache,
    host_name: HostName,
    *,
    selected_sections: SectionNameCollection,
) -> dict[SectionName, SectionMeta]:
    def needs_redetection(section_name: SectionName) -> bool:
        section = agent_based_register.get_section_plugin(section_name)
        return len(agent_based_register.get_section_producers(section.parsed_section_name)) > 1

    checking_sections = _make_checking_sections(host_name, selected_sections=selected_sections)
    disabled_sections = config_cache.disabled_snmp_sections(host_name)
    return {
        name: SectionMeta(
            checking=name in checking_sections,
            disabled=name in disabled_sections,
            redetect=name in checking_sections and needs_redetection(name),
            fetch_interval=config_cache.snmp_fetch_interval(host_name, name),
        )
        for name in (checking_sections | disabled_sections)
    }


def _make_checking_sections(
    hostname: HostName,
    *,
    selected_sections: SectionNameCollection,
) -> frozenset[SectionName]:
    if selected_sections is not NO_SELECTION:
        checking_sections = selected_sections
    else:
        checking_sections = frozenset(
            agent_based_register.get_relevant_raw_sections(
                check_plugin_names=check_table.get_check_table(
                    hostname,
                    filter_mode=check_table.FilterMode.INCLUDE_CLUSTERED,
                    skip_ignored=True,
                ).needed_check_names(),
                inventory_plugin_names=(),
            )
        )
    return frozenset(
        s for s in checking_sections if agent_based_register.is_registered_snmp_section_plugin(s)
    )


class _Builder:
    """Build a source list from host config and raw sections."""

    def __init__(
        self,
        host_name: HostName,
        ipaddress: HostAddress | None,
        *,
        config_cache: ConfigCache,
        selected_sections: SectionNameCollection,
        on_scan_error: OnError,
        force_snmp_cache_refresh: bool,
        simulation_mode: bool,
        file_cache_options: FileCacheOptions,
        file_cache_max_age: MaxAge,
    ) -> None:
        super().__init__()
        self.host_name: Final = host_name
        self.config_cache: Final = config_cache
        self.ipaddress: Final = ipaddress
        self.selected_sections: Final = selected_sections
        self.on_scan_error: Final = on_scan_error
        self.force_snmp_cache_refresh: Final = force_snmp_cache_refresh
        self.simulation_mode: Final = simulation_mode
        self.file_cache_options: Final = file_cache_options
        self.file_cache_max_age: Final = file_cache_max_age
        self._elems: dict[str, tuple[SourceInfo, FileCache, Fetcher]] = {}

        self._initialize()

    @property
    def sources(self) -> Sequence[tuple[SourceInfo, FileCache, Fetcher]]:
        # Always execute piggyback at the end
        return sorted(
            self._elems.values(),
            key=lambda args: (
                args[0].fetcher_type is FetcherType.PIGGYBACK,
                args[0].ident,
            ),
        )

    def _initialize(self) -> None:
        if self.config_cache.is_cluster(self.host_name):
            # Cluster hosts do not have any actual data sources
            # Instead all data is provided by the nodes
            return

        self._initialize_agent_based()
        self._initialize_snmp_based()
        self._initialize_mgmt_boards()

    def _initialize_agent_based(self) -> None:
        # agent-based data sources use the cache and persisted directories
        # that existed before the data source concept has been added where
        # each data source has its own set of directories.
        #
        # TODO: We should cleanup these old directories one day, then we can
        #       remove this special case.
        #
        if self.config_cache.is_all_agents_host(self.host_name):
            self._add(*self._get_agent())
            for elem in self._get_special_agents():
                self._add(*elem)

        elif self.config_cache.is_all_special_agents_host(self.host_name):
            for elem in self._get_special_agents():
                self._add(*elem)

        elif self.config_cache.is_tcp_host(self.host_name):
            special_agents = tuple(self._get_special_agents())
            if special_agents:
                self._add(*special_agents[0])
            else:
                self._add(*self._get_agent())

        if "no-piggyback" not in self.config_cache.tag_list(self.host_name):
            source = SourceInfo(
                self.host_name,
                self.ipaddress,
                "piggyback",
                FetcherType.PIGGYBACK,
                SourceType.HOST,
            )
            self._add(
                source,
                self.config_cache.make_piggyback_fetcher(source.hostname, source.ipaddress),
                AgentFileCache(
                    source.hostname,
                    path_template=make_file_cache_path_template(
                        fetcher_type=source.fetcher_type, ident=source.ident
                    ),
                    max_age=self.file_cache_max_age,
                    use_outdated=self.file_cache_options.use_outdated,
                    simulation=False,  # TODO Quickfix for SUP-9912
                    use_only_cache=False,
                    file_cache_mode=FileCacheMode.DISABLED,
                ),
            )

    def _initialize_snmp_plugin_store(self) -> None:
        if len(SNMPFetcher.plugin_store) != agent_based_register.len_snmp_sections():
            # That's a hack.
            #
            # `make_plugin_store()` depends on
            # `iter_all_snmp_sections()` and `iter_all_inventory_plugins()`
            # that are populated by the Check API upon loading the plugins.
            #
            # It is there, when the plugins are loaded, that we should
            # make the plugin store.  However, it is not clear whether
            # the API would let us register hooks to accomplish that.
            #
            # The current solution is brittle in that there is not guarantee
            # that all the relevant plugins are loaded at this point.
            SNMPFetcher.plugin_store = make_plugin_store()

    def _initialize_snmp_based(self) -> None:
        if not self.config_cache.is_snmp_host(self.host_name):
            return
        self._initialize_snmp_plugin_store()
        source = SourceInfo(
            self.host_name,
            self.ipaddress,
            "snmp",
            FetcherType.SNMP,
            SourceType.HOST,
        )
        self._add(
            source,
            SNMPFetcher(
                sections=make_sections(
                    self.config_cache,
                    self.host_name,
                    selected_sections=self.selected_sections,
                ),
                on_error=self.on_scan_error,
                missing_sys_description=self.config_cache.missing_sys_description(self.host_name),
                do_status_data_inventory=(
                    self.config_cache.hwsw_inventory_parameters(
                        self.host_name
                    ).status_data_inventory
                ),
                section_store_path=make_persisted_section_dir(source),
                snmp_config=self.config_cache.make_snmp_config(source.hostname, source.ipaddress),
            ),
            SNMPFileCache(
                source.hostname,
                path_template=make_file_cache_path_template(
                    fetcher_type=source.fetcher_type, ident=source.ident
                ),
                max_age=(
                    MaxAge.none() if self.force_snmp_cache_refresh else self.file_cache_max_age
                ),
                use_outdated=(
                    self.simulation_mode
                    or (
                        False
                        if self.force_snmp_cache_refresh
                        else self.file_cache_options.use_outdated
                    )
                ),
                simulation=self.simulation_mode,
                use_only_cache=False,
                file_cache_mode=self.file_cache_options.file_cache_mode(),
            ),
        )

    def _initialize_mgmt_boards(self) -> None:
        protocol = self.config_cache.management_protocol(self.host_name)
        if protocol is None:
            return

        self._initialize_snmp_plugin_store()
        ip_address = config.lookup_mgmt_board_ip_address(self.config_cache, self.host_name)
        if ip_address is None:
            # HostAddress is not Optional.
            #
            # See above.
            return
        if protocol == "snmp":
            source = SourceInfo(
                self.host_name,
                self.ipaddress,
                "mgmt_snmp",
                FetcherType.SNMP,
                SourceType.MANAGEMENT,
            )
            self._add(
                source,
                SNMPFetcher(
                    sections=make_sections(
                        self.config_cache,
                        self.host_name,
                        selected_sections=self.selected_sections,
                    ),
                    on_error=self.on_scan_error,
                    missing_sys_description=self.config_cache.missing_sys_description(
                        self.host_name
                    ),
                    do_status_data_inventory=(
                        self.config_cache.hwsw_inventory_parameters(
                            self.host_name
                        ).status_data_inventory
                    ),
                    section_store_path=make_persisted_section_dir(source),
                    snmp_config=self.config_cache.make_snmp_config(
                        source.hostname, source.ipaddress
                    ),
                ),
                SNMPFileCache(
                    source.hostname,
                    path_template=make_file_cache_path_template(
                        fetcher_type=source.fetcher_type, ident=source.ident
                    ),
                    max_age=(
                        MaxAge.none() if self.force_snmp_cache_refresh else self.file_cache_max_age
                    ),
                    use_outdated=(
                        self.simulation_mode
                        or (
                            False
                            if self.force_snmp_cache_refresh
                            else self.file_cache_options.use_outdated
                        )
                    ),
                    simulation=self.simulation_mode,
                    use_only_cache=False,
                    file_cache_mode=self.file_cache_options.file_cache_mode(),
                ),
            )
        elif protocol == "ipmi":
            source = SourceInfo(
                self.host_name,
                ip_address,
                "mgmt_ipmi",
                FetcherType.IPMI,
                SourceType.MANAGEMENT,
            )
            assert source.ipaddress
            self._add(
                source,
                self.config_cache.make_ipmi_fetcher(self.host_name, source.ipaddress),
                AgentFileCache(
                    source.hostname,
                    path_template=make_file_cache_path_template(
                        fetcher_type=source.fetcher_type, ident=source.ident
                    ),
                    max_age=self.file_cache_max_age,
                    use_outdated=self.simulation_mode or self.file_cache_options.use_outdated,
                    simulation=self.simulation_mode,
                    use_only_cache=False,
                    file_cache_mode=self.file_cache_options.file_cache_mode(),
                ),
            )
        else:
            raise LookupError()

    def _add(self, source: SourceInfo, fetcher: Fetcher, file_cache: FileCache) -> None:
        self._elems[source.ident] = (
            source,
            file_cache,
            fetcher,
        )

    def _get_agent(self) -> tuple[SourceInfo, Fetcher, FileCache]:
        datasource_program = self.config_cache.datasource_program(self.host_name)
        if datasource_program is not None:
            source = SourceInfo(
                self.host_name,
                self.ipaddress,
                "agent",
                FetcherType.PROGRAM,
                SourceType.HOST,
            )
            return (
                source,
                ProgramFetcher(
                    cmdline=core_config.translate_ds_program_source_cmdline(
                        datasource_program, self.host_name, self.ipaddress
                    ),
                    stdin=None,
                    is_cmc=config.is_cmc(),
                ),
                AgentFileCache(
                    source.hostname,
                    path_template=make_file_cache_path_template(
                        fetcher_type=source.fetcher_type, ident=source.ident
                    ),
                    max_age=self.file_cache_max_age,
                    use_outdated=self.simulation_mode or self.file_cache_options.use_outdated,
                    simulation=self.simulation_mode,
                    use_only_cache=False,
                    file_cache_mode=self.file_cache_options.file_cache_mode(),
                ),
            )

        connection_mode = self.config_cache.agent_connection_mode(self.host_name)
        if connection_mode == "push-agent":
            source = SourceInfo(
                self.host_name,
                self.ipaddress,
                "push-agent",
                FetcherType.PUSH_AGENT,
                SourceType.HOST,
            )
            # convert to seconds and add grace period
            interval = int(1.5 * 60 * self.config_cache.check_mk_check_interval(self.host_name))
            return (
                source,
                NoFetcher(),
                AgentFileCache(
                    source.hostname,
                    path_template=make_file_cache_path_template(
                        fetcher_type=source.fetcher_type, ident=source.ident
                    ),
                    max_age=MaxAge(interval, interval, interval),
                    use_outdated=self.simulation_mode or self.file_cache_options.use_outdated,
                    simulation=self.simulation_mode,
                    use_only_cache=True,
                    file_cache_mode=(
                        # Careful: at most read-only!
                        FileCacheMode.DISABLED
                        if self.file_cache_options.disabled
                        else FileCacheMode.READ
                    ),
                ),
            )
        if connection_mode == "pull-agent":
            source = SourceInfo(
                self.host_name,
                self.ipaddress,
                "agent",
                FetcherType.TCP,
                SourceType.HOST,
            )
            return (
                source,
                self.config_cache.make_tcp_fetcher(source.hostname, source.ipaddress),
                AgentFileCache(
                    source.hostname,
                    path_template=make_file_cache_path_template(
                        fetcher_type=source.fetcher_type, ident=source.ident
                    ),
                    max_age=self.file_cache_max_age,
                    use_outdated=self.simulation_mode or self.file_cache_options.use_outdated,
                    simulation=self.simulation_mode,
                    use_only_cache=self.file_cache_options.tcp_use_only_cache,
                    file_cache_mode=self.file_cache_options.file_cache_mode(),
                ),
            )
        raise NotImplementedError(f"connection mode {connection_mode!r}")

    def _get_special_agents(self) -> Iterable[tuple[SourceInfo, Fetcher, FileCache]]:
        def make_id(agentname: str) -> str:
            return f"special_{agentname}"

        for agentname, params in self.config_cache.special_agents(self.host_name):
            source = SourceInfo(
                self.host_name,
                self.ipaddress,
                make_id(agentname),
                FetcherType.SPECIAL_AGENT,
                SourceType.HOST,
            )
            fetcher = ProgramFetcher(
                cmdline=core_config.make_special_agent_cmdline(
                    self.host_name,
                    self.ipaddress,
                    agentname,
                    params,
                ),
                stdin=core_config.make_special_agent_stdin(
                    self.host_name,
                    self.ipaddress,
                    agentname,
                    params,
                ),
                is_cmc=config.is_cmc(),
            )
            file_cache = AgentFileCache(
                source.hostname,
                path_template=make_file_cache_path_template(
                    fetcher_type=source.fetcher_type, ident=source.ident
                ),
                max_age=self.file_cache_max_age,
                use_outdated=self.simulation_mode or self.file_cache_options.use_outdated,
                simulation=self.simulation_mode,
                use_only_cache=False,
                file_cache_mode=self.file_cache_options.file_cache_mode(),
            )
            yield source, fetcher, file_cache


def make_sources(
    host_name: HostName,
    ipaddress: HostAddress | None,
    *,
    config_cache: ConfigCache,
    force_snmp_cache_refresh: bool = False,
    selected_sections: SectionNameCollection = NO_SELECTION,
    on_scan_error: OnError = OnError.RAISE,
    simulation_mode: bool,
    file_cache_options: FileCacheOptions,
    file_cache_max_age: MaxAge,
) -> Sequence[tuple[SourceInfo, FileCache, Fetcher]]:
    """Sequence of sources available for `host_config`."""
    return _Builder(
        host_name,
        ipaddress,
        config_cache=config_cache,
        selected_sections=selected_sections,
        on_scan_error=on_scan_error,
        force_snmp_cache_refresh=force_snmp_cache_refresh,
        simulation_mode=simulation_mode,
        file_cache_options=file_cache_options,
        file_cache_max_age=file_cache_max_age,
    ).sources


def fetch_all(
    sources: Iterable[tuple[SourceInfo, FileCache, Fetcher]],
    *,
    mode: Mode,
) -> Sequence[tuple[SourceInfo, result.Result[AgentRawData | SNMPRawData, Exception], Snapshot]]:
    console.verbose("%s+%s %s\n", tty.yellow, tty.normal, "Fetching data".upper())
    return [
        do_fetch(source_info, file_cache, fetcher, mode=mode)
        for source_info, file_cache, fetcher in sources
    ]


def do_fetch(
    source_info: SourceInfo,
    file_cache: FileCache,
    fetcher: Fetcher,
    *,
    mode: Mode,
) -> tuple[SourceInfo, result.Result[AgentRawData | SNMPRawData, Exception], Snapshot]:
    console.vverbose(f"  Source: {source_info}\n")
    with CPUTracker() as tracker:
        raw_data = get_raw_data(file_cache, fetcher, mode)
    return source_info, raw_data, tracker.duration
