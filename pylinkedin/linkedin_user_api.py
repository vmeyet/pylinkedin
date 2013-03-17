import oauth2 as oauth
import urllib

# import time
# import datetime

from linkedin_api import LinkedinAPI


class LinkedinUserAPI(LinkedinAPI):
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

    CONNECTIONS_UPDATED = 'updated'
    CONNECTIONS_NEW = 'new'

    def __init__(self, consumer, access_token):
        LinkedinAPI.__init__(self, consumer)

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
            kwargs['selectors'] = ','.join(kwargs['selectors'])

        headers = kwargs.get('headers', {})
        if kwargs.get('languages'):
            if isinstance(kwargs['languages'], str):
                headers['Accept-Language'] = kwargs['languages']
            else:
                headers['Accept-Language'] = ', '.join(kwargs['languages'])
        kwargs['headers'] = headers

    def _api_call(self, api_endpoint, **kwargs):
        '''generic method to call the api.
            Param:
                kwargs -- 'get_parameters' (dict) -- dictionary of parameters
                                        to append to the url
                          'id' (int/str) -- profile id to fetch
                          'ids' (list/tuple) -- list of profile to fetch
                          'language' (str/tuple/list) -- preferred language/list of language
                                        ex: ('es-ES', 'en-US', 'it-IT')
                                        or: 'en-US, it-IT'
                          'profile_ids' (list/tuple) -- list of profile to fetch
                                        with the type of the profile id
                                        ex: ('~', 'id=1234', 'url=urlencoded-url-here')
                          'profile_url' (str) -- url of the profile to fetch
                          selectors (list/tuple) -- list of LinkedIn compatible
                                        field selectors
            Return:
                dict: response -- dictionary of the requested fields
        '''
        kwargs = self._handle_kwargs(kwargs)

        profile_id = kwargs.get('profile_id', '/~')

        content = self.get(
            endpoint=api_endpoint.format(profile_id=profile_id),
            fields=kwargs.get('selectors'),
            params=kwargs.get('get_parameters'),
            headers=kwargs.get('headers')
        )

        return content

    # PROFILE API

    def get_profile(self, selectors=None, **kwargs):
        return self._api_call(
            api_endpoint=self.URL_ENDPOINT['people'] + '{profile_id}',
            selectors=selectors,
            **kwargs
        )

    def get_connection(
        self, limit=None, skip=None, modified=None, modified_since=None, **kwargs
    ):
        get_parameters = kwargs.get('get_parameters', {})

        # limit and skip have more semantic
        if limit:
            get_parameters['count'] = limit
        if skip:
            get_parameters['start'] = skip
        if modified and modified in (self.CONNECTIONS_NEW, self.CONNECTIONS_UPDATED):
            get_parameters['modified'] = modified

        kwargs['get_parameters'] = get_parameters

        return self._api_call(
            api_endpoint=self.URL_ENDPOINT['people'] + '{profile_id}/connections',
            **kwargs
        )

    # PEOPLE SEARCH API

    def search_people(self):
        pass
