#!/usr/bin/env python
#pylint: disable=C0325, W0212
from __future__ import print_function

import sys
import os
import io
import json
import argparse
try:
    import configparser
except ImportError:
    import ConfigParser as configparser
    
from apimetrics.errors import APImetricsError
from apimetrics.api import APImetricsAPI

class CliHandler(object):

    def __init__(self, apimetrics, command_type, command, command_opt):
        self.apimetrics = apimetrics

        self.command_type = command_type
        self.command = command
        self.command_opt = command_opt

    def run(self, **kwargs):
        
        print('Command {}, type {}'.format(self.command, self.command_type))

        if self.command == 'list':
            if self.command_type not in ['auth']:
                func = getattr(self.apimetrics, 'list_all_{}s'.format(self.command_type))
            else:
                func = getattr(self.apimetrics, 'list_all_{}'.format(self.command_type))
            resp = func(**kwargs)

            for i, obj in enumerate(resp['results']):
                if self.command_type != 'deployment':
                    print(u'{index}: {id} - {name}'.format(index=i+1, id=obj['id'], name=obj.get('meta', {}).get('name')))
                else:
                    print(u'{index}: {id} - {target_id} @{frequency}m +{run_delay}s'.format(index=i+1, **obj))
            
        if self.command == 'create':
            string_input = u'\n'.join([x for x in sys.stdin])
            print(string_input)
            obj = json.loads(string_input)
            func = getattr(self.apimetrics, 'create_{}'.format(self.command_type))
            resp = func(obj, **kwargs)
            print(json.dumps(resp, indent=2))

        if self.command == 'read':
            func = getattr(self.apimetrics, 'get_{}'.format(self.command_type))
            resp = func(self.command_opt, **kwargs)
            print(json.dumps(resp, indent=2))

        if self.command == 'update':
            string_input = u''.join([x for x in sys.stdin])
            print(string_input)
            try:
                obj = json.loads(string_input)
            except:
                raise APImetricsError('Input is not JSON')
            func = getattr(self.apimetrics, 'update_{}'.format(self.command_type))
            resp = func(self.command_opt, obj, **kwargs)
            print(json.dumps(resp, indent=2))

        if self.command == 'delete':
            func = getattr(self.apimetrics, 'delete_{}'.format(self.command_type))

            inp_str = raw_input('Enter "YES" to confirm that you want to delete all: ')
            if inp_str == "YES":
                for i, obj in enumerate(resp['results']):
                    resp2 = func(obj['id'], **kwargs)
                    print(u'{}: {}'.format(i, resp2['status']))

        if self.command == 'deploy' and self.command_type in ['call', 'workflow']:
            run_delay = 10
            for i, obj in enumerate(resp['results']):
                resp2 = self.apimetrics.create_deployment(
                    {
                        'target_key': obj['id'],
                        'remote_location': '',
                        'frequency': 60*6,
                        'run_delay': run_delay
                    })
                run_delay += 10
                print(u'{}: {}'.format(i, resp2['run_delay']))
        
        if self.command == 'results':
            more = True
            cursor = None
            print('[\n')
            while more:
                resp = self.apimetrics.list_results(call_id=self.command_type, cursor=cursor)
                more = resp['meta']['more']
                cursor = resp['meta']['next_cursor']
                strings = []
                for result in resp['results']:
                    strings.append(json.dumps(result, indent=2))
                print(u',\n'.join(strings))
                if more:
                    print(',\n') # Keep JSON valid
            print(']\n')

def get_argument_parser():
    def add_common_args(parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--list', '-l', help="List objects", action="store_true")
        group.add_argument('--create', '-c', help="Create object", action="store_true")
        group.add_argument('--read', '-r', '--view', help="Read object as JSON by id")
        group.add_argument('--update', '-u', help="Update object by id")
        group.add_argument('--delete', '-d', help="Delete object by id")
        #parser.add_argument('--deploy', '-p', help="Deploy objects")
        #parser.add_argument('--results', '-r', help="View API call results")

    parser = argparse.ArgumentParser()

    apim_group = parser.add_argument_group('apimetrics', 'APImetrics settings')
    apim_group.add_argument('--apimetrics', '-a', help='Set the APImetrics key to use')
    apim_group.add_argument('--config', '-cfg', help='Set the config file to use')
    apim_group.add_argument('--dont-call-apimetrics', '-n', help='Don\'t call the APImetrics API', action="store_true")

    #script_opts = parser.add_argument_group('script', 'Script options')
    subparsers = parser.add_subparsers(help='sub-command help')
    
    # create the parser for the models
    for model in ('auth', 'call', 'deployment', 'report', 'token', 'workflow', 'alert', 'notification'):
        sub_parser = subparsers.add_parser(model, help='{} help'.format(model))
        sub_parser.set_defaults(command_type=model)
        add_common_args(sub_parser)

    return parser

def get_script_args(args):
    command_type = args.get('command_type')
    command = None
    command_opt = None

    command_opts = ('list', 'create', 'read', 'update', 'delete')
    for cmd in command_opts:
        if args.get(cmd, None):
            command = cmd
            command_opt = args.get(cmd)
            break

    script_args = {
        'command_type': command_type,
        'command': command,
        'command_opt': command_opt
    }
    return script_args

def get_apimetrics_args(args):

    config_file, config = open_config_file(args)

    apimetrics_key = config.get('APImetrics', 'apimetrics_key') if config_file else None

    apimetrics_args = {
        'apimetrics_key': args.get('apimetrics') or apimetrics_key,
        'api_base_url': config.get('APImetrics', 'base_url') if config.has_option('APImetrics', 'base_url') else None,
        'dont_call_apimetrics': args.get('dont_call_apimetrics') or False,
    }

    print(apimetrics_args)

    if config_file and apimetrics_args['apimetrics_key'] and apimetrics_args['apimetrics_key'] != apimetrics_key:
        with open(config_file, 'w') as config_file:
            config.set('APImetrics', 'apimetrics_key', apimetrics_args['apimetrics_key'])
            config.write(config_file)

    return apimetrics_args

def open_config_file(args):
    config_file = ['/etc/APImetrics', os.path.expanduser('~/.APImetrics'), 'apimetrics.ini']
    default_config = "[APImetrics]\napimetrics_key = "

    cfg = configparser.ConfigParser(allow_no_value=True)
    if sys.version_info[0] >= 3:
        cfg.readfp(io.StringIO(default_config))
    else:
        cfg.readfp(io.BytesIO(default_config))
    if args['config']:    
        config_file = args['config']
    success_files = cfg.read(config_file)

    if success_files:
        config_file = success_files[-1]
    else:
        print("Unable to find any config files to open!")
        config_file = None

    return config_file, cfg

def main():
    parser = get_argument_parser()
    args = vars(parser.parse_args())
    apimetrics_args = get_apimetrics_args(args)
    apimetrics = APImetricsAPI(**apimetrics_args)
    script_args = get_script_args(args)
    handler = CliHandler(apimetrics, **script_args)
    try:
        handler.run()
    except APImetricsError as ex:
        print("ERROR: {}".format(ex.message), file=sys.stderr)

