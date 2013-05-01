import oauth2 as oauth

import utils
from api import Api
from user_api_queryset import UserApiQueryset


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

    @property
    @utils.Memoize
    def profile(self):
        return self.get_profile()

    @property
    @utils.Memoize
    def connections(self):
        return self.get_connections()

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
