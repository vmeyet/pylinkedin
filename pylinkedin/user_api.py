import oauth2 as oauth
import urllib

import copy
import time
from datetime import datetime, date

from api import Api
from errors import UnavailableMethodForEndpointError


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
            accepted_keywords=(
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
        '''Intialization method
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
        self.filters = {}
        self.selectors = kwargs.get('selectors', [])

        self._current = 0

    # {{{ Private decorator

    def _watch(value):
        def decorator(fn):
            def wrapper(self, *args, **kwargs):
                old_value = copy.copy(getattr(self, value))

                ret_val = fn(self, *args, **kwargs)

                if old_value != getattr(self, value):
                    self.reset()

                return ret_val
            return wrapper
        return decorator

    # }}}

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

        if headers:
            kwargs['headers'] = headers

        return kwargs

    @classmethod
    def _selectors_to_string(cls, list_of_selectors):
        '''Transform the selectors' tuple into a string to append to the enpoint path
            Param:
                list_of_selectors (tuple/list) -- selectors to transform, they can be nested
            Return:
                (str) -- stringified version of those selectors
                         ex:

                        _selectors_to_string(
                            ('id', 'first-name', 'last-name', {'positions': ('title',)})
                        )

                        would return

                        :(id,first-name,last-name,positions:(title))
        '''
        selectors = [
            str(x) if not isinstance(x, dict)
            else ','.join(str(y) + cls._selectors_to_string(x[y]) for y in x)
            for x in list_of_selectors
        ]
        return ':(' + ','.join(selectors) + ')'

    @classmethod
    def _handle_filtering_values(cls, value):
        # linekdin api use timestamp since Epoch, this api can use date/datetime objects
        if isinstance(value, date):
            return int(time.mktime(value.timetuple()) * 1e3)
        return value

    # }}}

    def __call__(self):
        '''Call the api endpoint using the UserApi passed during the initialization
        '''

        self.kwargs['selectors'] = self.selectors
        kwargs = self._handle_kwargs(self.kwargs)

        profile_id = kwargs.get('profile_id', '/~')

        content = self.api.get(
            endpoint=self.api_endpoint.format(profile_id=profile_id) + kwargs.get('selectors', ''),
            params=self.filters,
            headers=kwargs.get('headers')
        )

        # li search api force us to do ugly stuff as the following
        content = content.get('people', content)

        return content

    def get(self):
        '''Same as call, but cache the result
        '''
        if not self._fetched_result:
            self._fetched_result = self.__call__()
        return self._fetched_result

    def __len__(self):
        if self.filters.get('count', False):
            return self.filters['count']
        result = self.get()
        return result.get('_total', len(result))

    def __iter__(self):
        return self

    def next(self):
        # TODO: there is a nasty infinite loop here
        if self._current > self.__len__():
            raise StopIteration
        self._current += 1
        return self[self._current - 1]  # test with: self._current - 1

    def __getitem__(self, key):
        result = self.get()
        skip = result.get('_start')
        limit = result.get('_count')
        if skip is not None and limit is not None:
            # this mean linkedin have been paginating the result
            new_skip = 0
            if key < skip or key >= skip + limit:
                new_skip = int(key / limit) * limit
                key -= new_skip
            result = self.skip(new_skip).limit(limit).get()
        return result.get('values', []).__getitem__(key)

    def reset(self):
        self._fetched_result = None
        self._current = 0

    # {{{ Filtering methods and aliases

    @_watch('filters')
    def filter(self, **kwargs):
        return self._filter(**kwargs)

    def _filter(self, **kwargs):
        '''Allows filtering over the api result. this correspond to the GET parameters
        that can be pass to the api. If filters change, any previous cached result is
        erased and another call to the api is made
        '''
        self.filters.update({
            k.replace('_', '-'): self._handle_filtering_values(v)
            for k, v in kwargs.iteritems() if k in self.accepted_keywords
        })
        return self

    def limit(self, limit):
        '''Alias for filtering using the 'count' GET parameter
        '''
        if not 'count' in self.accepted_keywords:
            raise UnavailableMethodForEndpointError('limit', self.endpoint)
        return self._filter(count=limit)

    def skip(self, skip):
        '''Alias for filtering using the 'skip' GET parameter
        '''
        if not 'start' in self.accepted_keywords:
            raise UnavailableMethodForEndpointError('count', self.endpoint)
        return self._filter(start=skip)

    def sort(self, keyword):
        '''Alias for filtering using the 'sort' GET parameter
        '''
        if not 'sort' in self.accepted_keywords:
            raise UnavailableMethodForEndpointError('sort', self.endpoint)
        return self.filter(sort=keyword)

    # }}}

    def count(self):
        '''alias for __len__
        '''
        return self.__len__()

    @_watch('selectors')
    def select(self, *selectors):
        '''Set the linekdin selectors to use during the api call
        '''
        self.selectors = selectors
        return self
