import oauth2 as oauth
import urllib

import time
from datetime import datetime

from api import Api


class UserApi(Api):
    '''Api abstraction specific to a given user, using his tokens
    '''

    URL_ENDPOINT = {
        'people': '/v1/people',
        'people_search': '/v1/people-search',
        'groups': '/v1/groups',
        'post': '/v1/posts',
        'companie': '/v1/companies',
        'company_search': '/v1/company-search',
        'jobs': '/v1/jobs',
        'job_search': '/v1/job-search',
    }

    def __init__(self, api_key, api_secret, access_token):
        Api.__init__(self, api_key, api_secret)

        self.oauth_token = oauth.Token(
            access_token['oauth_token'], access_token['oauth_token_secret']
        )
        self.client = oauth.Client(self.consumer, self.oauth_token)

    def _handle_kwargs(self, kwargs):
        if not kwargs:
            return

        profile_id = None
        if kwargs.get('id'):
            profile_id = '/id=%s' % kwargs['id']
        elif kwargs.get('ids'):
            profile_id = '::(id=%s)' % ',id='.join(map(str, kwargs['ids']))
        elif kwargs.get('profile_ids'):
            profile_id = '::(%s)' % ','.join(kwargs['profile_ids'])
        elif kwargs.get('profile_url'):
            profile_id = '/url=%s' % urllib.urlencode(kwargs['profile_url'])
        if profile_id:
            kwargs['profile_id'] = profile_id

        if kwargs.get('selectors'):
            kwargs['selectors'] = self._selectors_to_string(kwargs['selectors'])

        headers = kwargs.get('headers', {})
        if kwargs.get('language'):
            if isinstance(kwargs['language'], str):
                headers['Accept-Language'] = kwargs['language']
            else:
                headers['Accept-Language'] = ', '.join(kwargs['language'])
        kwargs['headers'] = headers
        return kwargs

    def _api_call(self, api_endpoint, **kwargs):
        '''generic method to call the api.
            Param:
                api_endpoint -- url endpoint of the LI api to call
                kwargs -- 'get_parameters' (dict) -- dictionary of parameters
                                        to append to the url
                          'id' (int/str) -- profile id to fetch
                          'ids' (list/tuple) -- list of profile to fetch
                          'language' (str/tuple/list) -- preferred language/list of languages
                                        ex: ('es-ES', 'en-US', 'it-IT')
                                        or: 'en-US, it-IT'
                          'profile_ids' (list/tuple) -- list of profile to fetch
                                        with the type of the profile id
                                        ex: ('~', 'id=1234', 'url=urlencoded-url-here')
                          'profile_url' (str) -- url of the profile to fetch
                          'selectors' (list/tuple) -- list of LinkedIn compatible
                                        field selectors
            Return:
                dict: response -- dictionary of the requested fields
        '''
        kwargs = self._handle_kwargs(kwargs)

        profile_id = kwargs.get('profile_id', '/~')

        content = self.get(
            endpoint=api_endpoint.format(profile_id=profile_id) + kwargs.get('selectors'),
            params=kwargs.get('get_parameters'),
            headers=kwargs.get('headers')
        )

        return content

    def _api_call_with_get_parameter(self, api_endpoint, accepted_keywords, **kwargs):
        get_parameters = kwargs.get('get_parameters', {})

        get_parameters = {
            k.replace('_', '-'): v
            for k, v in kwargs.iteritems() if k in accepted_keywords
        }

        if limit:
            get_parameters['count'] = limit
        if skip:
            get_parameters['start'] = skip

        kwargs['get_parameters'] = get_parameters

        return self._api_call(
            api_endpoint=api_endpoint,
            **kwargs
        )

    @classmethod
    def _selectors_to_string(cls, list_of_selector):
        selectors = [
            str(x) if not isinstance(x, dict)
            else ','.join(str(y) + cls._selectors_to_string(x[y]) for y in x)
            for x in list_of_selector
        ]
        return ':(' + ','.join(selectors) + ')'

    # PROFILE API

    def get_profile(self, selectors=None, **kwargs):
        return self._api_call(
            api_endpoint=self.URL_ENDPOINT['people'] + '{profile_id}',
            selectors=selectors,
            **kwargs
        )

    def get_connection(
        self, modified=None, modified_since=None, **kwargs
    ):
        if modified and modified in ('new', 'updated'):
            kwargs['modified'] = modified

        if modified_since and isinstance(modified_since, datetime):
            kwargs['modified_since'] = time.mktime(modified_since.timetuple())

        return _api_call_with_get_parameter(
            api_endpoint=self.URL_ENDPOINT['people'] + '{profile_id}/connections',
            accepted_keywords=('modified', 'modified_since'),
            **kwargs
        )

    # PEOPLE SEARCH API

    def search_people(self, **kwargs):
        return self._api_call_with_get_parameter(
            api_endpoint=self.URL_ENDPOINT['people_search'],
            accepted_keyword=(
                'keywords', 'first_name', 'last_name', 'company_name', 'current_company',
                'title', 'current_title', 'school_name', 'current_school', 'postal_code',
                'distance', 'facet', 'facets', 'sort'
            ),
            **kwargs
        )
