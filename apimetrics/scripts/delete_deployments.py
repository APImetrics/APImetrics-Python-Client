#!/usr/bin/env python
from __future__ import print_function
import logging
import os
import re
import sys
from six.moves import input
import apimetrics

logging.basicConfig(
    stream=sys.stdout,
    format='%(asctime)s:%(levelname)s: %(message)s',
    level=os.environ.get('DEBUG_LEVEL') or logging.INFO)

log = logging.getLogger(__name__)  # pylint: disable=C0103


class DeploymentsRemover(apimetrics.APImetricsCLI):

    # Overriding APImetricsCLI to add our command-line specific commands
    def get_argument_parser(self):
        parser = super(DeploymentsRemover, self).get_argument_parser()

        parser.add_argument('--non-interactive', '-y', help="Interactive mode, ask for each API call", action="store_true", default=False)
        parser.add_argument('--name', '-n', help="Only APIs which match this name")

        return parser

    def ask_user_about_call(self, call):
        if self.args.get('name'):
            api_name = call['meta']['name']
            if not re.search(self.args.get('name'), api_name):
                return False
        if not self.args.get('non_interactive'):
            inp_str = input('Delete deployments for API call "{name}"? y/N: '.format(**call.get('meta')))
            return inp_str.lower() == 'y'
        return True

    def run(self, **kwargs):
        list_of_calls = self.api.list_all_calls(**kwargs)
        for call in list_of_calls['results']:
            if self.ask_user_about_call(call):
                deployments = self.api.list_deployments_by_call(call=call['id'], **kwargs)

                for deployment in deployments['results']:
                    print('Deleting deployment {location_id}...'.format(**deployment.get('deployment')), end='\t\t')
                    self.api.delete_deployment(deployment['id'], **kwargs)
                    print('OK')

def main():
    cli = DeploymentsRemover()
    try:
        cli.run()
    except apimetrics.APImetricsError as ex:
        print("ERROR: {}".format(ex), file=sys.stderr)

if __name__ == '__main__':
    main()
