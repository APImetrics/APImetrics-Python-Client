#!/usr/bin/env python
#pylint: disable=C0325, W0212, R0903, R0912, R0915
from __future__ import print_function
import logging
import sys
import os
import io
import json
import argparse
from six.moves import input, configparser
from apimetrics.errors import APImetricsError
from apimetrics.api import APImetricsAPI

logging.basicConfig(
    stream=sys.stdout,
    format='%(asctime)s:%(levelname)s: %(message)s',
    level=os.environ.get('DEBUG_LEVEL') or logging.INFO)

log = logging.getLogger(__name__)  # pylint: disable=C0103

# Generic class for handling command-line interaction with the APImetrics API
class APImetricsCLI(object):

    def __init__(self, api_class=APImetricsAPI):
        self._args = None
        self.parser = self.get_argument_parser()
        apimetrics_args = self.get_apimetrics_args()
        self.api = api_class(**apimetrics_args)

    @property
    def args(self):
        if not self._args:
            self._args = vars(self.parser.parse_args())
        return self._args

    # Override this method to add more arguments to your script
    def get_argument_parser(self):

        parser = argparse.ArgumentParser(fromfile_prefix_chars='@')

        apim_group = parser.add_argument_group('apimetrics', 'APImetrics settings')
        apim_group.add_argument('--apimetrics', '-a', help='Set the APImetrics key to use')
        apim_group.add_argument('--config', '-cfg', help='Set the config file to use')
        apim_group.add_argument('--simulate', '-s', help='Simulate - don\'t call the APImetrics API', action="store_true")

        return parser

    def get_apimetrics_args(self):
        config_file, config = self.open_config_file()
        apimetrics_key = config.get('APImetrics', 'apimetrics_key') if config_file else None

        apimetrics_args = {
            'apimetrics_key': self.args.get('apimetrics') or apimetrics_key,
            'api_base_url': config.get('APImetrics', 'base_url') if config.has_option('APImetrics', 'base_url') else None,
            'simulate': self.args.get('simulate') or False,
        }

        if config_file and apimetrics_args['apimetrics_key'] and apimetrics_args['apimetrics_key'] != apimetrics_key:
            with open(config_file, 'w') as config_file:
                config.set('APImetrics', 'apimetrics_key', apimetrics_args['apimetrics_key'])
                config.write(config_file)

        return apimetrics_args

    def open_config_file(self):
        config_file = ['/etc/APImetrics', os.path.expanduser('~/.APImetrics'), 'apimetrics.ini']
        default_config = "[APImetrics]\napimetrics_key = "

        cfg = configparser.ConfigParser(allow_no_value=True)

        if sys.version_info[0] >= 3:
            cfg.readfp(io.StringIO(default_config))
        else:
            cfg.readfp(io.BytesIO(default_config))

        if self.args['config']:
            config_file = self.args['config']
        success_files = cfg.read(config_file)

        if success_files:
            config_file = success_files[-1]
        else:
            log.warn("Unable to find any config files to open!")
            config_file = None

        return config_file, cfg

# Class to handle the commands for this specific script
class APImetricsScript(APImetricsCLI):

    # Overriding APImetricsCLI to add our command-line specific commands
    def get_argument_parser(self):

        def add_common_args(parser):
            group = parser.add_mutually_exclusive_group(required=True)
            group.add_argument('--list', '-l', help="List objects", action="store_true")
            group.add_argument('--create', '-c', help="Create object", action="store_true")
            group.add_argument('--read', '-r', '--view', help="Read object as JSON by id")
            group.add_argument('--update', '-u', help="Update object by id")
            group.add_argument('--delete', '-d', help="Delete object by id")
            #parser.add_argument('--deploy', '-p', help="Deploy objects")
            #parser.add_argument('--results', '-r', help="View API call results")

        parser = super(APImetricsScript, self).get_argument_parser()
        subparsers = parser.add_subparsers(help='sub-command help')
        # create the parser for the models
        for model in ('auth', 'call', 'deployment', 'report', 'token', 'workflow', 'alert', 'notification'):
            sub_parser = subparsers.add_parser(model, help='{} help'.format(model))
            sub_parser.set_defaults(command_type=model)
            add_common_args(sub_parser)

        return parser

    # Additioanl commands for command-line
    def get_script_args(self):
        command_type = self.args.get('command_type')
        command = None
        command_opt = None

        command_opts = ('list', 'create', 'read', 'update', 'delete')
        for cmd in command_opts:
            if self.args.get(cmd, None):
                command = cmd
                command_opt = self.args.get(cmd)
                break

        return command_type, command, command_opt


    def list(self, command_type, _, **kwargs):
        if command_type not in ['auth']:
            func = getattr(self.api, 'list_all_{}s'.format(command_type))
        else:
            func = getattr(self.api, 'list_all_{}'.format(command_type))
        resp = func(**kwargs)

        for i, obj in enumerate(resp['results']):
            if command_type != 'deployment':
                print(u'{index}: {id} - {name}'.format(index=i+1, id=obj['id'], name=obj.get('meta', {}).get('name')))
            else:
                print(u'{index}: {id} - {target_id} @{frequency}m +{run_delay}s'.format(index=i+1, id=obj.get('id'), **obj.get('deployment')))

    def create(self, command_type, _, **kwargs):
        string_input = u'\n'.join([x for x in sys.stdin])
        print(string_input)
        obj = json.loads(string_input)
        func = getattr(self.api, 'create_{}'.format(command_type))
        resp = func(obj, **kwargs)
        print(json.dumps(resp, indent=2))

    def read(self, command_type, command_opt, **kwargs):
        func = getattr(self.api, 'get_{}'.format(command_type))
        resp = func(command_opt, **kwargs)
        print(json.dumps(resp, indent=2))
        return resp

    def update(self, command_type, command_opt, **kwargs):
        string_input = u''.join([x for x in sys.stdin])
        print(string_input)
        try:
            obj = json.loads(string_input)
        except:
            raise APImetricsError('Input is not JSON')
        func = getattr(self.api, 'update_{}'.format(command_type))
        resp = func(command_opt, obj, **kwargs)
        print(json.dumps(resp, indent=2))

    def delete(self, command_type, command_opt, **kwargs):
        resp = self.read(command_type, command_opt, **kwargs)
        func = getattr(self.api, 'delete_{}'.format(command_type))
        inp_str = input('Enter "YES" to confirm that you want to delete all: ')
        if inp_str == "YES":
            for i, obj in enumerate(resp['results']):
                resp2 = func(obj['id'], **kwargs)
                print(u'{}: {}'.format(i, resp2['status']))

    def deploy(self, command_type, command_opt, **kwargs):
        if command_type in ['call', 'workflow']:
            resp = self.read(command_type, command_opt, **kwargs)
            run_delay = 10
            for i, obj in enumerate(resp['results']):
                resp2 = self.api.create_deployment(
                    {
                        'target_key': obj['id'],
                        'remote_location': '',
                        'frequency': 60*6,
                        'run_delay': run_delay
                    })
                run_delay += 10
                print(u'{}: {}'.format(i, resp2['run_delay']))

    def results(self, command_type, _, **kwargs):
        more = True
        cursor = None
        print('[\n')
        while more:
            resp = self.api.list_results(call_id=command_type, cursor=cursor, **kwargs)
            more = resp['meta']['more']
            cursor = resp['meta']['next_cursor']
            strings = []
            for result in resp['results']:
                strings.append(json.dumps(result, indent=2))
            print(u',\n'.join(strings))
            if more:
                print(',\n') # Keep JSON valid
        print(']\n')

    def run(self, **kwargs):
        command_type, command, command_opt = self.get_script_args()
        print('Command {}, type {}'.format(command, command_type))
        command_fn = getattr(self, command)
        command_fn(command_type, command_opt, **kwargs)

def main():
    cli = APImetricsScript()
    try:
        cli.run()
    except APImetricsError as ex:
        print("ERROR: {}".format(ex), file=sys.stderr)
