import json
import urllib
import urlparse
import oauth2 as oauth

from errors import LinkedinApiError


class Api(object):

    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret

        self.base_url = 'https://api.linkedin.com'
        self.consumer = oauth.Consumer(api_key, api_secret)
        self.client = oauth.Client(self.consumer)

        self.headers = {'User-agent': 'pylinkedin'}
        self._format = None
        self.use_json()

        self._handler_POST_body = {
            'json': json.dumps,
            'urlencoded': urllib.urlencode
        }

    def api_request(self, endpoint, method='GET', params=None, headers=None, client=None):
        url = self.base_url + endpoint
        client = client if client else self.client
        params = params if params else {}
        headers = headers if headers else {}

        headers.update(self.headers)

        if method == 'POST':
            resp, content = client.request(
                uri=url,
                method='POST',
                body=self._handler_POST_body[self._format](params),
                headers=headers
            )

        else:
            resp, content = client.request(
                uri='%s?%s' % (url, urllib.urlencode(params)),
                method='GET',
                headers=headers
            )

        # It's Better to Beg for Forgiveness than to Ask for Permission
        # Let's first try to decode json from the response
        try:
            content = json.loads(content)
        except ValueError:
            try:
                content = dict(urlparse.parse_qsl(content))
            except ValueError:
                raise LinkedinApiError(
                    'Unable to decode li api response.\ncontent: %s' % content
                )

        status = int(resp.get('status', 0))
        if status < 200 or status >= 300:
            raise LinkedinApiError(
                'Error Code: %d, Response content: %s' % (status, content)
            )

        return content if content else True

    def get(
        self, endpoint, params=None, headers=None, client=None
    ):
        return self.api_request(
            endpoint=endpoint, params=params, headers=headers, client=client
        )

    def post(
        self, endpoint, params=None, headers=None, client=None
    ):
        return self.api_request(
            endpoint=endpoint, method='POST', params=params, headers=headers, client=client
        )

    def use_json(self):
        self.headers.update({
            'x-li-format': 'json',
            'Content-Type': 'application/json'
        })
        self._format = 'json'

    def use_urlencoded(self):
        self.headers.pop('x-li-format', None)
        self.headers['Content-Type'] = 'application/x-www-form-urlencoded'
        self._format = 'urlencoded'
