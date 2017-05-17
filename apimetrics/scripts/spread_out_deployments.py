#!/usr/bin/env python
from __future__ import print_function
import logging
import os
import sys
import itertools
import math
import apimetrics

logging.basicConfig(
    stream=sys.stdout,
    format='%(asctime)s:%(levelname)s: %(message)s',
    level=os.environ.get('DEBUG_LEVEL') or logging.INFO)

log = logging.getLogger(__name__)  # pylint: disable=C0103

def _index_of_first(lst, pred):
    for i, item in enumerate(lst):
        if pred(item):
            return i
    return None


class TidyDeploymentsScript(apimetrics.APImetricsCLI):  # pylint: disable=R0903

    def run(self, **kwargs):  # pylint: disable=R0914

        deployments = self.api.list_all_deployments(**kwargs).get('results')

        all_deployments = sorted(deployments, key=lambda deploy: deploy.get('deployment', {}).get('run_delay'))

        frequencies = sorted(set(deploy.get('deployment', {}).get('frequency') for deploy in deployments))

        for freq in frequencies:

            log.info('Frequency: %d', freq)

            deployments = [deploy for deploy in all_deployments if deploy.get('deployment', {}).get('frequency') == freq]
            locations = sorted(set(deploy.get('deployment', {}).get('location_id') for deploy in deployments if deploy.get('deployment', {}).get('frequency') == freq))
            targets = sorted(set(deploy.get('deployment', {}).get('target_id') for deploy in deployments if deploy.get('deployment', {}).get('frequency') == freq))

            loc_len = len(locations)
            trg_len = len(targets)
            dep_len = len(deployments)
            total = loc_len * trg_len

            log.debug("Locations: %s", locations)
            log.debug("Targets: %s", [t[-8:] for t in targets])

            combos = list(itertools.product(locations, targets))
            output = []

            log.debug("Total: %d, Potential Max: %d", dep_len, total)

            while combos:
                j = 0
                for i in range(total):

                    trg_ind = i % trg_len
                    combo = None

                    while combo not in combos:
                        loc_ind = j % loc_len
                        combo = (locations[loc_ind], targets[trg_ind])
                        j += 1

                    if combo in combos:

                        def index_of_matching(loc, trg):
                            def match(deploy):
                                return deploy.get('deployment', {}).get('location_id') == loc and deploy.get('deployment', {}).get('target_id') == trg
                            return match

                        deploy_ind = _index_of_first(deployments, index_of_matching(*combo))
                        if deploy_ind is not None:
                            # print(deploy_ind, combo)
                            output.append(deployments[deploy_ind])
                        else:
                            log.debug('SKIP %s', combo)
                        combos.remove(combo)

                    j += 1

            gap_per_deploy = (freq * 60) / float(dep_len + 1)  # Skip the 0 run_delay for everywhere

            for index0, deploy in enumerate(output):

                index = index0 + 1
                info = deploy.get('deployment', {})
                location_id = info.get('location_id')
                target_id = info.get('target_id')

                new_run_delay = int(math.ceil(index * gap_per_deploy))

                freq = info.get('frequency')

                info_str = "ID: {} \t Freq: {} \t {} -> {} \t {} \t {}".format(deploy['id'][-8:], freq, info['run_delay'], new_run_delay, target_id[-8:], location_id)
                log.info(info_str)

                if new_run_delay != info['run_delay']:
                    self.api.update_deployment(
                        obj_id=deploy['id'],
                        obj={
                            'deployment': {
                                'run_delay': new_run_delay
                            }
                        },
                        **kwargs)

def main():
    cli = TidyDeploymentsScript()
    try:
        cli.run()
    except apimetrics.APImetricsError as ex:
        print("ERROR: {}".format(ex), file=sys.stderr)

if __name__ == '__main__':
    main()
