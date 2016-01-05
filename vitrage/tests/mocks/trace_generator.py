# Copyright 2015 - Alcatel-Lucent
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

__author__ = 'erosensw'

"""
Mock event generator.

Generator will generate events for a specific entity type, as defined
by a configuration file. A single generator can generate events for
multiple instances of the same entity type.

"""

from random import randint

import exrex

from vitrage.tests.mocks.entity_model import BasicEntityModel as bem
import vitrage.tests.mocks.utils as utils

DYNAMIC_INFO_FKEY = 'filename'
STATIC_INFO_FKEY = 'static_filename'
NAME_KEY = 'name'
MAPPING_KEY = 'mapping'
EXTERNAL_INFO_KEY = 'external'

NUM_EVENTS = '#events'
GENERATOR = 'generator'


# specification files for input types
# Mock synchronizer specs
SYNC_INST_SNAPSHOT_D = 'dynamic_snapshot.json'
SYNC_INST_SNAPSHOT_S = 'static_snapshot.json'
SYNC_INST_UPDATE_D = 'dynamic_update.json'

# Mock transformer Specs (i.e., what the transformer outputs)
TRANS_INST_SNAPSHOT_D = 'transformer_inst_snapshot_dynamic.json'
TRANS_INST_SNAPSHOT_S = 'transformer_inst_snapshot_static.json'
HOST_SNAPSHOT_D = 'transformer_host_snapshot_dynamic.json'
HOST_SNAPSHOT_S = 'transformer_host_snapshot_static.json'
ZONE_SNAPSHOT_D = 'transformer_zone_snapshot_dynamic.json'
ZONE_SNAPSHOT_S = 'transformer_zone_snapshot_static.json'


class EventTraceGenerator(object):
    """A generator for event traces.

    A generator can generate events for several instances of the same type,
    though with different static parameters (ids etc.).

    A generator generates event based on (a) dynamic content JSON file,
    (b) static content JSON file, and (c) mapping info to other entities,
    such as host-to-vm mapping.

    File is expected to be in the ../resources folder
    """

    def __init__(self, spec):
        """Initializes the trace generator according to the specs.

        NOTE: The dynamic file given determines the manner in which information
        is extracted and overlapped between the three sources of info.
        Any new spec file needs to be added here as well.

        :param spec: specification of the trace characteristics.
        :type spec: dict
        Sample format:
        {
        tg.DYNAMIC_INFO_FKEY: tg.TRANS_INST_SNAPSHOT_D, # dynamic info file
        tg.STATIC_INFO_FKEY: tg.TRANS_INST_SNAPSHOT_S, # static info file
        tg.MAPPING_KEY: mapping,  # inter-entity mapping, e.g., vm-host
        tg.NAME_KEY: 'Instance (vm) snapshot generator', # name for gen
        tg.NUM_EVENTS: 10 # how many events of this type to generate
         }
        """

        static_info_parsers = \
            {SYNC_INST_SNAPSHOT_D: _get_sync_vm_snapshot_values,
             SYNC_INST_UPDATE_D: _get_sync_vm_update_values,
             TRANS_INST_SNAPSHOT_D: _get_trans_vm_snapshot_values,
             HOST_SNAPSHOT_D: _get_host_snapshot_values,
             ZONE_SNAPSHOT_D: _get_zone_snapshot_values}

        dynam_specs = utils.load_specs(spec[DYNAMIC_INFO_FKEY])
        dynamic_spec_filename = spec[DYNAMIC_INFO_FKEY].split('/')[-1]
        static_specs = static_info_parsers[dynamic_spec_filename](spec)
        self.name = spec.get(NAME_KEY, 'generator')

        self._models = [bem(dynam_specs, details) for details in static_specs]

    @property
    def models(self):
        """Returns the individual entity models for this generator.

        :return: the individual entity models for this generator.
        :rtype: list
        """

        return self._models


def generate_data_stream(models, event_num=100):
    """Generates a list of events.

    :param event_num: number of events to generate
    :type event_num: int
    :return: list of generated events
    :rtype: list
    """

    instance_num = len(models)
    data_stream = []
    for _ in xrange(event_num):
        random_model = models[randint(0, instance_num - 1)]
        data_stream.append(random_model.params)
    return data_stream


def _get_sync_vm_snapshot_values(spec):
    """Generates the static synchronizer values for each vm.

    :param spec: specification of event generation.
    :type spec: dict
    :return: list of static synchronizer values for each vm.
    :rtype: list
    """

    vm_host_mapping = spec[MAPPING_KEY]
    static_info_re = None
    if spec[STATIC_INFO_FKEY] is not None:
        static_info_re = utils.load_specs(spec[STATIC_INFO_FKEY])
    static_values = []
    host_ids = {}
    for vm_name, host_name in vm_host_mapping:
        if host_name not in host_ids.keys():
            host_ids[host_name] = exrex.getone('[0-9a-f]{56}')

        mapping = {'hostid': host_ids[host_name],
                   'hostname': host_name,
                   "OS-EXT-SRV-ATTR:host": host_name,
                   "OS-EXT-SRV-ATTR:hypervisor_hostname": host_name,
                   'name': vm_name}
        static_values.append(combine_data(
            static_info_re, mapping, spec.get(EXTERNAL_INFO_KEY, None)
        ))
    return static_values


def _get_trans_vm_snapshot_values(spec):
    """Generates the static transformer values for each vm.

    :param spec: specification of event generation.
    :type spec: dict
    :return: list of static transformer values for each vm.
    :rtype: list
    """

    vm_host_mapping = spec[MAPPING_KEY]
    static_info_re = None
    if spec[STATIC_INFO_FKEY] is not None:
        static_info_re = utils.load_specs(spec[STATIC_INFO_FKEY])
    static_values = []
    for vm_name, host_name in vm_host_mapping:
        mapping = {'hostname': host_name,
                   'id': vm_name,
                   'name': vm_name}
        static_values.append(combine_data(
            static_info_re, mapping, spec.get(EXTERNAL_INFO_KEY, None)
        ))

    return static_values


def _get_sync_vm_update_values(spec):
    """Generates the static synchronizer values for each vm, for updates.

    :param spec: specification of event generation.
    :type spec: dict
    :return: list of static synchronizer values for each vm updates.
    :rtype: list
    """

    vm_host_mapping = spec[MAPPING_KEY]
    static_info_re = None
    if spec[STATIC_INFO_FKEY] is not None:
        static_info_re = utils.load_specs(spec[STATIC_INFO_FKEY])
    static_values = []
    for vm_name, host_name in vm_host_mapping:
        mapping = {'payload': {'host': host_name,
                               'display_name': vm_name}}
        static_values.append(combine_data(
            static_info_re, mapping, spec.get(EXTERNAL_INFO_KEY, None)
        ))

    return static_values


def _get_host_snapshot_values(spec):
    """Generates the static synchronizer values for each host.

        :param spec: specification of event generation.
        :type spec: dict
        :return: list of static synchronizer values for each host.
        :rtype: list
        """

    host_zone_mapping = spec[MAPPING_KEY]
    static_info_re = None
    if spec[STATIC_INFO_FKEY] is not None:
        static_info_re = utils.load_specs(spec[STATIC_INFO_FKEY])
    static_values = []
    for host_name, zone_name in host_zone_mapping:
        mapping = {'zone_id': zone_name,
                   'name': host_name,
                   'id': host_name}
        static_values.append(combine_data(
            static_info_re, mapping, spec.get(EXTERNAL_INFO_KEY, None)
        ))

    return static_values


def _get_zone_snapshot_values(spec):
    """Generates the static synchronizer values for each zone.

    :param spec: specification of event generation.
    :type spec: dict
    :return: list of static synchronizer values for each zone.
    :rtype: list
    """

    zone_node_mapping = spec[MAPPING_KEY]
    static_info_re = None
    if spec[STATIC_INFO_FKEY] is not None:
        static_info_re = utils.load_specs(spec[STATIC_INFO_FKEY])
    static_values = []
    for zone_name, node_name in zone_node_mapping:
        mapping = {'name': zone_name,
                   'id': zone_name}
        static_values.append(combine_data(
            static_info_re, mapping, spec.get(EXTERNAL_INFO_KEY, None)
        ))

    return static_values


def combine_data(static_info_re, mapping_info, external_info):
    if external_info:
        mapping_info = utils.merge_vals(mapping_info, external_info)
    static_info = utils.generate_vals(static_info_re)
    return utils.merge_vals(static_info, mapping_info)


def get_trace_generators(entity_spec_list, default_events=100):
    """Returns a collection of event generators.

    :param entity_spec_list: list of generator specs.
    :type entity_spec_list: list
    :return: list of generators
    :rtype: list

    """

    generator_spec_list = \
        [
            {GENERATOR: EventTraceGenerator(entity_spec),
             NUM_EVENTS: entity_spec.get(NUM_EVENTS, default_events)}
            for entity_spec in entity_spec_list
            ]
    return generator_spec_list