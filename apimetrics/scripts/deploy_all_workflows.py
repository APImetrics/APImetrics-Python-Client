#!/usr/bin/env python
from __future__ import print_function
import logging
import os
import sys
import math
import random
import re
from six.moves import input
import apimetrics

logging.basicConfig(
    stream=sys.stdout,
    format='%(asctime)s:%(levelname)s: %(message)s',
    level=os.environ.get('DEBUG_LEVEL') or logging.INFO)

log = logging.getLogger(__name__)  # pylint: disable=C0103


class DeploymentCreator(apimetrics.APImetricsCLI):

    # Overriding APImetricsCLI to add our command-line specific commands
    def get_argument_parser(self):
        parser = super(DeploymentCreator, self).get_argument_parser()

        parser.add_argument('location_ids', metavar='LOC', nargs='+', help="Location ID to deploy to")
        parser.add_argument('--frequency', '-f', type=int, help="Frequency to make API call (minutes)")
        parser.add_argument('--interactive', '-i', help="Interactive mode, ask for each API call", action="store_true")
        parser.add_argument('--name', '-n', help="Only APIs which match this name")

        return parser

    def ask_user_about_call(self, call):
        if self.args.get('name'):
            api_name = call['meta']['name']
            if not re.search(self.args.get('name'), api_name):
                return False
        if self.args.get('interactive'):
            inp_str = input('Change deployments for Workflow "{name}"? y/N: '.format(**call.get('meta')))
            return inp_str.lower() == 'y'
        return True

    def run(self, **kwargs):

        list_of_calls = self.api.list_all_workflows(**kwargs)
        locations = list(self.args['location_ids'])

        for call in list_of_calls['results']:
            if self.ask_user_about_call(call):
                deployments = self.api.list_deployments_by_workflow(call=call['id'], **kwargs)

                for deployment in deployments['results']:
                    print('Deleting old deployment {location_id} for api {name}...'.format(name=call['meta']['name'], **deployment.get('deployment')), end='\t\t')
                    self.api.delete_deployment(deployment['id'], **kwargs)
                    print('OK')

                # Spread out API calls, avoid exactly on the hour etc
                frequency = self.args.get('frequency', 10)
                gap = math.ceil(float(frequency * 60) / (1.0 + len(self.args['location_ids'])))
                random.shuffle(locations)

                for i, location_id in enumerate(locations):
                    deployment = {
                        'deployment': {
                            'target_id': call['id'],
                            'location_id': location_id,
                            'frequency': frequency,
                            'run_delay': int((i + 1) * gap),
                        }
                    }
                    print('New deployment {location_id} for api {name}, freq {frequency}, delay {run_delay}s...'.format(name=call['meta']['name'], **deployment['deployment']), end='\t\t')
                    self.api.create_deployment(deployment, **kwargs)
                    print('OK')

def main():
    cli = DeploymentCreator()
    try:
        cli.run()
    except apimetrics.APImetricsError as ex:
        print("ERROR: {}".format(ex), file=sys.stderr)

if __name__ == '__main__':
    main()
