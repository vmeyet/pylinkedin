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


#     def clean_dates(self, content):
#         data = etree.fromstring(content)
#         for d in data.iter(tag=etree.Element):
#             try:
#                 trial = int(d.text)
#                 if len(d.text) > 8:
#                     dt = datetime.datetime.fromtimestamp(float(trial)/1000)
#                     d.text = dt.strftime('%m/%d/%Y %I:%M:%S')
#             except:
#                 continue
#         return etree.tostring(data)


    # def get_network_updates(self, access_token, **kwargs):
    #     """Get network updates for the current user.  Valid keyword arguments are
    #     "count", "start", "type", "before", and "after".  "Count" and "start" are for the number
    #     of updates to be returned.  "Type" specifies what type of update you are querying.
    #     "Before" and "after" set the time interval for the query.  Valid argument types are
    #     an integer representing UTC with millisecond precision or a Python datetime object.
    #     """
    #     if 'type' in kwargs.keys():
    #         assert type(kwargs['type']) == type(list()), 'Keyword argument "type" must be of type "list"'
    #         [self.check_network_code(c) for c in kwargs['type']]

    #     if 'before' in kwargs.keys():
    #         kwargs['before'] = self.dt_obj_to_string(kwargs['before']) if kwargs['before'] else None
    #     if 'after' in kwargs.keys():
    #         kwargs['after'] = self.dt_obj_to_string(kwargs['after']) if kwargs['after'] else None

    #     user_token, url = self.prepare_request(access_token, self.api_network_update_url, kwargs)
    #     client = oauth.Client(self.consumer, user_token)
    #     resp, content = client.request(url, 'GET')
    #     content = self.clean_dates(content)
    #     return LinkedInXMLParser(content).results

    # def get_comment_feed(self, access_token, network_key):
    #     """
    #     Get a comment feed for a particular network update.  Requires the update key
    #     for the network update as returned by the API.
    #     """
    #     url = re.sub(r'\{NETWORK UPDATE KEY\}', network_key, self.api_comment_feed_url)
    #     user_token, url = self.prepare_request(access_token, url)
    #     client = oauth.Client(self.consumer, user_token)
    #     resp, content = client.request(url, 'GET')
    #     content = self.clean_dates(content)
    #     return LinkedInXMLParser(content).results

    # def submit_comment(self, access_token, network_key, bd):
    #     """
    #     Submit a comment to a network update.  Requires the update key for the network
    #     update that you will be commenting on.  The comment body is the last positional
    #     argument.  NOTE: The XML will be applied to the comment for you.
    #     """
    #     bd_pre_wrapper = '<?xml version="1.0" encoding="UTF-8"?><update-comment><comment>'
    #     bd_post_wrapper = '</comment></update-comment>'
    #     xml_request = bd_pre_wrapper + bd + bd_post_wrapper
    #     url = re.sub(r'\{NETWORK UPDATE KEY\}', network_key, self.api_comment_feed_url)
    #     user_token, url = self.prepare_request(access_token, url)
    #     client = oauth.Client(self.consumer, user_token)
    #     resp, content = client.request(url, method='POST', body=xml_request, headers={'Content-Type': 'application/xml'})
    #     return content

    # def set_status_update(self, access_token, bd):
    #     """
    #     Set the status for the current user.  The status update body is the last
    #     positional argument.  NOTE: The XML will be applied to the status update
    #     for you.
    #     """
    #     bd_pre_wrapper = '<?xml version="1.0" encoding="UTF-8"?><current-status>'
    #     bd_post_wrapper = '</current-status>'
    #     xml_request = bd_pre_wrapper + bd + bd_post_wrapper
    #     user_token, url = self.prepare_request(access_token, self.api_update_status_url)
    #     client = oauth.Client(self.consumer, user_token)
    #     resp, content = client.request(url, method='PUT', body=xml_request)
    #     return content

    # def search(self, access_token, data, field_selector_string=None):
    #     """
    #     Use the LinkedIn Search API to find users.  The criteria for your search
    #     should be passed as the 2nd positional argument as a dictionary of key-
    #     value pairs corresponding to the paramters allowed by the API.  Formatting
    #     of arguments will be done for you (i.e. lists of keywords will be joined
    #     with "+")
    #     """
    #     srch = LinkedInSearchAPI(data, access_token, field_selector_string)
    #     client = oauth.Client(self.consumer, srch.user_token)
    #     rest, content = client.request(srch.generated_url, method='GET')
    #     # print content # useful for debugging...
    #     return LinkedInXMLParser(content).results

    # def send_message(self, access_token, recipients, subject, body):
    #     """
    #     Send a message to a connection.  "Recipients" is a list of ID numbers,
    #     "subject" is the message subject, and "body" is the body of the message.
    #     The LinkedIn API does not allow HTML in messages.  All XML will be applied
    #     for you.
    #     """
    #     assert type(recipients) == type(list()), '"Recipients argument" (2nd position) must be of type "list"'
    #     mxml = self.message_factory(recipients, subject, body)
    #     user_token, url = self.prepare_request(access_token, self.api_mailbox_url)
    #     client = oauth.Client(self.consumer, user_token)
    #     resp, content = client.request(url, method='POST', body=mxml, headers={'Content-Type': 'application/xml'})
    #     return content

    # def send_invitation(self, access_token, recipients, subject, body, **kwargs):
    #     """
    #     Send an invitation to a user.  "Recipients" is an ID number OR email address
    #     (see below), "subject" is the message subject, and "body" is the body of the message.
    #     The LinkedIn API does not allow HTML in messages.  All XML will be applied
    #     for you.

    #     NOTE:
    #     If you pass an email address as the recipient, you MUST include "first_name" AND
    #     "last_name" as keyword arguments.  Conversely, if you pass a member ID as the
    #     recipient, you MUST include "name" and "value" as keyword arguments.  Documentation
    #     for obtaining those values can be found on the LinkedIn website.
    #     """
    #     if 'first_name' in kwargs.keys():
    #         mxml = self.invitation_factory(recipients, subject, body,
    #                                     first_name=kwargs['first_name'], last_name=kwargs['last_name'])
    #     else:
    #         mxml = self.invitation_factory(recipients, subject, body,
    #                                     name=kwargs['name'], value=kwargs['value'])
    #     user_token, url = self.prepare_request(access_token, self.api_mailbox_url)
    #     client = oauth.Client(self.consumer, user_token)
    #     resp, content = client.request(url, method='POST', body=mxml, headers={'Content-Type': 'application/xml'})
    #     return content





#     def check_network_code(self, code):
#         if code not in self.valid_network_update_codes:
#             raise ValueError('Code %s not a valid update code' % code)


#     def dt_obj_to_string(self, dtobj):
#         if type(dtobj) == type(int()) or type(dtobj) == type(str()) or type(dtobj) == type(long()):
#             return dtobj
#         elif hasattr(dtobj, 'timetuple'):
#             return time.mktime(int(dtobj.timetuple())*1000)
#         else:
#             raise TypeError('Inappropriate argument type - use either a datetime object, \
#                             string, or integer for timestamps')

#     def message_factory(self, recipients, subject, body):
#         rec_path = '/people/'

#         E = ElementMaker()
#         MAILBOX_ITEM = E.mailbox_item
#         RECIPIENTS = E.recipients
#         RECIPIENT = E.recipient
#         PERSON = E.person
#         SUBJECT = E.subject
#         BODY = E.body

#         recs = [RECIPIENT(PERSON(path=rec_path+r)) for r in recipients]

#         mxml = MAILBOX_ITEM(
#             RECIPIENTS(
#                 *recs
#             ),
#             SUBJECT(subject),
#             BODY(body)
#         )
#         return re.sub('mailbox_item', 'mailbox-item', etree.tostring(mxml))

#     def invitation_factory(self, recipient, subject, body, **kwargs):
#         id_rec_path = '/people/id='
#         email_rec_path = '/people/email='

#         E = ElementMaker()
#         MAILBOX_ITEM = E.mailbox_item
#         RECIPIENTS = E.recipients
#         RECIPIENT = E.recipient
#         PERSON = E.person
#         SUBJECT = E.subject
#         BODY = E.body
#         CONTENT = E.item_content
#         REQUEST = E.invitation_request
#         CONNECT = E.connect_type
#         FIRST = E.first_name
#         LAST = E.last_name
#         AUTH = E.authorization
#         NAME = E.name
#         VALUE = E.value

#         if not '@' in recipient:
#             recs = RECIPIENT(PERSON(path=id_rec_path+r))
#             auth = CONTENT(REQUEST(CONNECT('friend'), AUTH(NAME(kwargs['name']), VALUE(kwargs['value']))))
#         else:
#             recs = RECIPIENT(
#                         PERSON(
#                             FIRST(kwargs['first_name']),
#                             LAST(kwargs['last_name']),
#                             path=email_rec_path+r
#                         )
#                     )
#             auth = CONTENT(REQUEST(CONNECT('friend')))
#         mxml = MAILBOX_ITEM(
#             RECIPIENTS(
#                 *recs
#             ),
#             SUBJECT(subject),
#             BODY(body),
#             auth
#         )
#         return re.sub('_', '-', etree.tostring(mxml))

# class LinkedInSearchAPI(LinkedInAPI):
#     def __init__(self, params, access_token, field_selector_string=None):
#         self.api_search_url = 'http://api.linkedin.com/v1/people-search'
#         if field_selector_string:
#             self.api_search_url += ':' + field_selector_string
#         self.routing = {
#             'keywords': self.keywords,
#             'name': self.name,
#             'current_company': self.current_company,
#             'current_title': self.current_title,
#             'location_type': self.location_type,
#             'network': self.network,
#             'sort_criteria': self.sort_criteria
#         }
#         self.user_token, self.generated_url = self.do_process(access_token, params)
#         print "url:", self.generated_url

#     def do_process(self, access_token, params):
#         assert type(params) == type(dict()), 'The passed parameters to the Search API must be a dictionary.'
#         user_token = oauth.Token(access_token['oauth_token'],
#                         access_token['oauth_token_secret'])
#         url = self.api_search_url
#         for p in params:
#             try:
#                 url = self.routing[p](url, params[p])
#                 params[p] = None
#             except KeyError:
#                 continue
#         remaining_params = {}
#         for p in params:
#             if params[p]:
#                 remaining_params[p] = params[p]
#         url = self.process_remaining_params(url, remaining_params)
#         return user_token, url

#     def process_remaining_params(self, url, ps):
#         prep_url = url
#         for p in ps:
#             try:
#                 prep_url = self.append_initial_arg(p, ps[p], prep_url)
#             except AssertionError:
#                 prep_url = self.append_sequential_arg(p, ps[p], prep_url)
#         return prep_url

#     def keywords(self, url, ps):
#         return self.list_argument(url, ps, 'keywords')

#     def name(self, url, ps):
#         return self.list_argument(url, ps, 'name')

#     def current_company(self, url, ps):
#         return self.true_false_argument(url, ps, 'current-company')

#     def current_title(self, url, ps):
#         return self.true_false_argument(url, ps, 'current-title')

#     def location_type(self, url, ps):
#         prep_url = url
#         assert ps in ['I', 'Y'], 'Valid parameter types for search-location-type are "I" and "Y"'
#         try:
#             prep_url = self.append_initial_arg('search-location-type', ps, prep_url)
#         except AssertionError:
#             prep_url = self.append_sequential_arg('search-location-type', ps, prep_url)
#         return prep_url

#     def network(self, url, ps):
#         prep_url = url
#         assert ps in ['in', 'out'], 'Valid parameter types for network are "in" and "out"'
#         try:
#             prep_url = self.append_initial_arg('network', ps, prep_url)
#         except AssertionError:
#             prep_url = self.append_sequential_arg('network', ps, prep_url)
#         return prep_url

#     def sort_criteria(self):
#         prep_url = url
#         assert ps in ['recommenders', 'distance', 'relevance'], 'Valid parameter types for sort-criteria \
#                             are "recommenders", "distance", and "relevance"'
#         try:
#             prep_url = self.append_initial_arg('sort-criteria', ps, prep_url)
#         except AssertionError:
#             prep_url = self.append_sequential_arg('sort-criteria', ps, prep_url)
#         return prep_url

#     def true_false_argument(self, url, ps, arg):
#         prep_url = url
#         if ps:
#             ps = 'true'
#         else:
#             ps = 'false'
#         try:
#             prep_url = self.append_initial_arg(arg, ps, prep_url)
#         except AssertionError:
#             prep_url = self.append_sequential_arg(arg, ps, prep_url)
#         return prep_url

#     def list_argument(self, url, ps, arg):
#         prep_url = url
#         li = '+'.join(ps)
#         try:
#             prep_url = self.append_initial_arg(arg, li, prep_url)
#         except AssertionError:
#             prep_url = self.append_sequential_arg(arg, li, prep_url)
#         return prep_url
