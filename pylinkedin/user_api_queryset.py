import copy
import urllib
import time
from datetime import datetime, date

from errors import UnavailableMethodForEndpointError


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

        self.kwargs['selectors'] = self.selectors if self.selectors else ''
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
        if self._current > self.__len__():
            raise StopIteration
        self._current += 1
        return self[self._current - 1]

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

    def first(self):
        try:
            return self[0]
        except:
            return None

    @_watch('selectors')
    def select(self, *selectors):
        '''Set the linekdin selectors to use during the api call
        '''
        self.selectors = selectors
        return self
