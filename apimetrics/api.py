#pylint: disable=C0325
from __future__ import print_function

import logging
import json
import requests

from apimetrics.errors import APImetricsError

#https://urllib3.readthedocs.org/en/latest/security.html#insecureplatformwarning
requests.packages.urllib3.disable_warnings()

def _get_list_method(obj_name, search_term=None):
    def list_obj(self, **kwargs):
        url = '{url}/{obj_name}/'
        if search_term:
            assert search_term in kwargs
            url += '{}/{}/'.format(search_term, kwargs[search_term])
            del kwargs[search_term]
        if not self.dont_call_apimetrics:
            full_url = url.format(url=self.API_BASE_URL, obj_name=obj_name)
            if self.debug:
                print(u'GET {}'.format(full_url))
            resp = requests.get(
                full_url,
                headers=self.headers,
                params=kwargs)
            return self._handle_resp(resp, 200)
        return {'results': [], 'meta': {'more': False, 'next_cursor': None}}
    return list_obj

def _get_list_all_method(obj_name, search_term=None):

    list_fn = _get_list_method(obj_name, search_term)
    def list_all_obj(self, **kwargs):
        output = {'results':[], 'meta': {'more': False, 'next_cursor': None}}
        more = True
        cursor = None
        while more:
            resp = list_fn(self, cursor=cursor, **kwargs)
            more = resp['meta']['more']
            cursor = resp['meta']['next_cursor']
            output['results'].extend(resp['results'])
        return output
    return list_all_obj

def _get_object_method(obj_name):
    def get_obj(self, obj_id, **kwargs):
        url = '{url}/{obj_name}/{obj_id}/'
        full_url = url.format(url=self.API_BASE_URL, obj_name=obj_name, obj_id=obj_id)
        if not self.dont_call_apimetrics:
            if self.debug:
                print(u'GET {}'.format(full_url))
            resp = requests.get(
                full_url,
                headers=self.headers,
                params=kwargs)
            return self._handle_resp(resp, 200)
        return {'id': obj_id}
    return get_obj

def _delete_object_method(obj_name):
    def del_obj(self, obj_id, **kwargs):
        url = '{url}/{obj_name}/{obj_id}/'
        if not self.dont_call_apimetrics:
            full_url = url.format(url=self.API_BASE_URL, obj_name=obj_name, obj_id=obj_id)
            if self.debug:
                print(u'DELETE {}'.format(full_url))
            resp = requests.delete(
                full_url,
                headers=self.headers,
                params=kwargs)
            return self._handle_resp(resp, 200)
        return {'id': obj_id}
    return del_obj

def _create_object_method(obj_name):
    def create_obj(self, obj, **kwargs):
        url = '{url}/{obj_name}/'
        full_url = url.format(url=self.API_BASE_URL, obj_name=obj_name)
        if self.debug:
            print(u'PUT {}'.format(full_url))
        if not self.dont_call_apimetrics:
            resp = requests.put(
                full_url,
                headers=self.post_headers,
                data=json.dumps(obj),
                params=kwargs)
            return self._handle_resp(resp, 201)
        obj['id'] = 'DUMMY'
        return obj
    return create_obj

def _update_object_method(obj_name):
    def update_obj(self, obj_id, obj, **kwargs):
        url = '{url}/{obj_name}/{obj_id}/'
        full_url = url.format(url=self.API_BASE_URL, obj_name=obj_name, obj_id=obj_id)
        if not self.dont_call_apimetrics:
            if self.debug:
                print(u'POST {}'.format(full_url))
            resp = requests.post(
                full_url,
                headers=self.post_headers,
                data=json.dumps(obj),
                params=kwargs)
            return self._handle_resp(resp, 200)
        return obj
    return update_obj

class APImetricsAPI(object):

    API_BASE_URL = "https://client.apimetrics.io/api/2"
    debug = True

    @property
    def headers(self):
        return {
            'Authorization': 'Bearer {token}'.format(token=self.apimetrics_key)
        }

    @property
    def post_headers(self):
        return {
            'Authorization': 'Bearer {token}'.format(token=self.apimetrics_key),
            'Content-Type': 'application/json'
        }

    def __init__(self, apimetrics_key=None, always_use_existing=False, always_create_new=False, dont_call_apimetrics=False, api_base_url=None):
        self.always_use_existing = always_use_existing
        self.always_create_new = always_create_new
        self.apimetrics_key = apimetrics_key if apimetrics_key else None
        self.dont_call_apimetrics = dont_call_apimetrics
        self.API_BASE_URL = api_base_url if api_base_url else self.API_BASE_URL
        if not self.apimetrics_key:
            raise APImetricsError("Missing APImetrics API key")

    list_auth = _get_list_method('auth')
    list_auth_by_domain = _get_list_method('auth', 'domain')
    list_calls = _get_list_method('calls')
    list_calls_by_auth = _get_list_method('calls', 'auth')
    list_deployments = _get_list_method('deployments')
    list_deployments_by_call = _get_list_method('deployments', 'call')
    list_deployments_by_workflow = _get_list_method('deployments', 'workflow')
    list_reports = _get_list_method('reports')
    list_tokens = _get_list_method('tokens')
    list_tokens_by_auth = _get_list_method('tokens', 'auth')
    list_workflows = _get_list_method('workflows')

    list_all_auth = _get_list_all_method('auth')
    list_all_auth_by_domain = _get_list_all_method('auth', 'domain')
    list_all_calls = _get_list_all_method('calls')
    list_all_calls_by_auth = _get_list_all_method('calls', 'auth')
    list_all_deployments = _get_list_all_method('deployments')
    list_all_deployments_by_call = _get_list_all_method('deployments', 'call')
    list_all_deployments_by_workflow = _get_list_all_method('deployments', 'workflow')
    list_all_reports = _get_list_all_method('reports')
    list_all_tokens = _get_list_all_method('tokens')
    list_all_tokens_by_auth = _get_list_all_method('tokens', 'auth')
    list_all_workflows = _get_list_all_method('workflows')

    get_auth = _get_object_method('auth')
    get_call = _get_object_method('calls')
    get_deployment = _get_object_method('deployments')
    get_report = _get_object_method('reports')
    get_token = _get_object_method('tokens')
    get_workflow = _get_object_method('workflows')

    create_auth = _create_object_method('auth')
    create_call = _create_object_method('calls')
    create_deployment = _create_object_method('deployments')
    create_report = _create_object_method('reports')
    create_token = _create_object_method('tokens')
    create_workflow = _create_object_method('workflows')

    update_auth = _update_object_method('auth')
    update_call = _update_object_method('calls')
    update_deployment = _update_object_method('deployments')
    update_report = _update_object_method('reports')
    update_token = _update_object_method('tokens')
    update_workflow = _update_object_method('workflows')

    delete_auth = _delete_object_method('auth')
    delete_call = _delete_object_method('calls')
    delete_deployment = _delete_object_method('deployments')
    delete_report = _delete_object_method('reports')
    delete_token = _delete_object_method('tokens')
    delete_workflow = _delete_object_method('workflows')

    def _handle_resp(self, resp, expected_status_code=200):
        try:
            output = resp.json()
        except ValueError:
            return APImetricsError(resp)
        if resp.status_code == expected_status_code:
            return output
        raise APImetricsError(output.get('error_msg', output))

    def _ask_user_for_pick(self, object_name, output):
        object_id = None

        if output:
            selected = -1

            if not self.always_use_existing and not self.always_create_new:
                print('0: Create new {}'.format(object_name))
                for i, service in enumerate(output):
                    print("{}: {}".format(i+1, service.get('name', 'NAME?')))

                selected = -1
                while selected < 0 or selected > len(output):
                    inp_str = raw_input('Enter number for {} to use: '.format(object_name))
                    try:
                        selected = int(inp_str)
                    except (ValueError, TypeError):
                        selected = -1
                selected -= 1

            elif self.always_use_existing:
                selected = 0

            if selected >= 0:
                object_id = output[selected]['id']

        return object_id

    def list_results(self, call_id, **kwargs):
        
        url = '{url}/calls/{call_id}/results/'

        resp = requests.get(
            url.format(url=self.API_BASE_URL, call_id=call_id),
            headers=self.headers,
            params=kwargs)

        return self._handle_resp(resp)

    # Calling this could take a *LONG* time
    def list_all_results(self, call_id, **kwargs):

        output = {'results':[], 'meta': {'more': False, 'next_cursor': None}}
        more = True
        cursor = None
        while more:
            resp = self.list_results(call_id, cursor=cursor, **kwargs)
            more = resp['meta']['more']
            cursor = resp['meta']['next_cursor']
            output['results'].extend(resp['results'])
        return output

