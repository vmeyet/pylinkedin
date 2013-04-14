import oauth2 as oauth
import urllib

import time
from datetime import datetime

from api import Api
from errors import LinkedinUserApiError


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

    # {{{ PROFILE API

    def get_profile(self, **kwargs):
        return UserApiQueryset(
            api=self,
            api_endpoint=self.URL_ENDPOINT['people'] + '{profile_id}',
            **kwargs
        ).get()

    def get_connections(self, **kwargs):
        return UserApiQueryset(
            api=self,
            api_endpoint=self.URL_ENDPOINT['people'] + '{profile_id}/connections',
            accepted_keywords=('modified', 'modified_since', 'start', 'count'),
            **kwargs
        )

    # }}}

    # {{{ PEOPLE SEARCH API

    def search_people(self, **kwargs):
        return UserApiQueryset(
            api=self,
            api_endpoint=self.URL_ENDPOINT['people_search'],
            accepted_keyword=(
                'keywords', 'first_name', 'last_name', 'company_name', 'current_company',
                'title', 'current_title', 'school_name', 'current_school', 'postal_code',
                'distance', 'facet', 'facets', 'sort', 'start', 'count'
            ),
            **kwargs
        )

    def get_out_of_network_profile(self, p_id, value, **kwargs):
        kwargs['headers'] = kwargs.get('headers', {})
        kwargs['headers'].update({'x-li-auth-token': value})
        return UserApiQueryset(
            api=self,
            api_endpoint=self.URL_ENDPOINT['people'] + '/%s' % p_id,
            headers=kwargs.pop('headers'),
            **kwargs
        ).get()

    # }}}

    # {{{ GROUP API

    def get_group(self):
        pass

    # }}}


class UserApiQueryset(object):

    def __init__(self, api, api_endpoint, accepted_keywords=None, **kwargs):
        ''' intialization method
            Param:
                api (UserApi) -- the user api element referring to (needed for the api call)
                api_endpoint (path) -- endpoint of the api to call
                accepted_keywords -- keywords that can be used to filter result
                           (correspond to get_parameters)
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
        self.api = api
        self._fetched_result = None
        self.api_endpoint = api_endpoint
        self.accepted_keywords = accepted_keywords
        self.kwargs = kwargs
        self.filter_params = {}

    # {{{ Private class methods

    @classmethod
    def _handle_kwargs(cls, kwargs):
        if not kwargs:
            return {}

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
            kwargs['selectors'] = cls._selectors_to_string(kwargs['selectors'])

        headers = kwargs.get('headers', {})
        if kwargs.get('language'):
            if isinstance(kwargs['language'], str):
                headers['Accept-Language'] = kwargs['language']
            else:
                headers['Accept-Language'] = ', '.join(kwargs['language'])
        kwargs['headers'] = headers
        return kwargs

    @classmethod
    def _selectors_to_string(cls, list_of_selector):
        selectors = [
            str(x) if not isinstance(x, dict)
            else ','.join(str(y) + cls._selectors_to_string(x[y]) for y in x)
            for x in list_of_selector
        ]
        return ':(' + ','.join(selectors) + ')'

    @classmethod
    def _handle_filtering_values(cls, value):
        # linekdin api use timestamp since Epoch, this api can use date/datetime objects
        if isinstance(value, date):
            return time.mktime(value.timetuple())
        return value

    # }}}

    def __call__(self):

        kwargs = self._handle_kwargs(self.kwargs)

        profile_id = kwargs.get('profile_id', '/~')

        content = self.api.get(
            endpoint=self.api_endpoint.format(profile_id=profile_id) + kwargs.get('selectors', ''),
            params=self.filter_params,
            headers=kwargs.get('headers')
        )

        return content

    def get(self):
        if not self._fetched_result:
            self._fetched_result = self.__call__()
        return self._fetched_result

    def __len__(self):
        result = self.get()
        return result.get('_total', len(result))

    def __iter__(self):
        result = self.get()
        return result.get('values', []).__iter__()

    def __getitem__(self, key):
        result = self.get()
        return result.get('values', []).__getitem__(key)

    def filter(self, **kwargs):
        self._fetched_result = None

        self.filter_params = self.filter_params.update({
            k.replace('_', '-'): self._handle_filtering_values(v)
            for k, v in kwargs.iteritems() if k in self.accepted_keywords
        })

        return self

    def limit(self, limit):
        if not 'count' in self.accepted_keywords:
            raise LinkedinUserApiError(
                'Cannot use method "limit" on the endpoint %s' % self.endpoint
            )
        return self.filter(count=limit)

    def skip(self, skip):
        if not 'start' in self.accepted_keywords:
            raise LinkedinUserApiError(
                'Cannot use method "count" on the endpoint %s' % self.endpoint
            )
        return self.filter(start=skip)

    def sort(self, keyword):
        if not 'sort' in self.accepted_keywords:
            raise LinkedinUserApiError(
                'Cannot use method "sort" on the endpoint %s' % self.endpoint
            )
        return self.filter(sort=keyword)

    def select(self, *selectors):
        self._fetched_result = None
        self.kwargs.update({'selectors': selectors})
        return self
