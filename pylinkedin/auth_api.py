import urllib
import oauth2 as oauth

from api import Api
from user_api import UserApi


class AuthApi(Api):

    def __init__(self, api_key, api_secret):
        self.request_token_endpoint = '/uas/oauth/requestToken'
        self.access_token_endpoint = '/uas/oauth/accessToken'
        # self.authorize_endpoint = '/uas/oauth/authorize'

        Api.__init__(self, api_key, api_secret)

    def get_access_token(self, request_token, verifier):
        '''Get a permanent token using the oauth verifier and request token
        '''
        token = oauth.Token(
            request_token['oauth_token'],
            request_token['oauth_token_secret']
        )
        token.set_verifier(verifier)

        self.use_urlencoded()
        return self.post(
            endpoint=self.access_token_endpoint,
            client=oauth.Client(self.consumer, token)
        )

    def get_request_token_and_auth_url(self, redirect_url=None, permissions=None):
        '''Get a request token from linkedin api, based on the consumer
        key and secret
            Param:
                redirect_url (url) -- the callback url, hit by linkedin if
                                     the user authenticate successfully
            Return:
                request_token (dict) -- the request token that came back from
                                       linkedin api
                auth_url (url) -- the authentication url to give to the user.
        '''
        self.use_urlencoded()
        request_token = self.post(
            endpoint=self.request_token_endpoint,
            params=self._get_additional_parameters(redirect_url, permissions)

        )
        auth_url = self._create_auth_url_from_request_token(
            request_token=request_token
        )

        return request_token, auth_url

    def get_user_api_from(self, access_token):
        return UserApi(self.api_key, self.api_secret, access_token)

    def _create_auth_url_from_request_token(self, request_token):
        url = request_token['xoauth_request_auth_url'] + '?' + urllib.urlencode({
            'oauth_token': request_token['oauth_token'],
        })
        return url

    def _get_additional_parameters(self, redirect_url, permissions):
        if not redirect_url and not permissions:
            return dict()

        data = dict()
        if redirect_url:
            data['oauth_callback'] = urllib.quote_plus(redirect_url)
        if permissions:
            if isinstance(permissions, (list, tuple)):
                permissions = ' '.join(permissions)
            data['scope'] = permissions
        return data
