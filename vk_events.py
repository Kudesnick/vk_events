# -*- coding: utf-8 -*-

# vkontakte ====================================================================

import requests

app_id = 2685278 # KateMobile

class vk:
    __api_v = '5.199'
    definitely_id = 1
    possibly_id = 2

    def __init__(self, vk_token: str):
        self.__token = vk_token
        data = {'access_token': self.__token, 'v': self.__api_v, 'fields': 'timezone'}

        response = requests.post('https://api.vk.com/method/users.get', data = data)
        if not response: exit(-1)
        print('url "{}" response text: {}'.format(response.url, response.text))
        self.__user_id = response.json()['response'][0]['id']
        self.timezone = int(response.json()['response'][0]['timezone'])

    def get_events(self, time: int = 0):
        data = {
            'access_token': self.__token,
            'v': self.__api_v,
            'user_id': self.__user_id,
            'filter': 'events',
            'extended': 1,
            'fields': 'start_date,finish_date,addresses,member_status'
        }

        response = requests.post('https://api.vk.com/method/groups.get', data = data)
        if not response: exit(-1)
        print('url "{}" response text: {}'.format(response.url, response.text))

        self.events = [{k: v for k, v in i.items() if not 'photo' in k} for i in response.json()['response']['items'] if i['start_date'] >= time]

        print('{} events after filtered'.format(len(self.events)))
        return len(self.events)

    def events_verbose(self, color_scheme: dict, time: int = 0):
        if not hasattr(self, 'events'):
            self.get_events(time)

        for e in self.events:
            e['location'] = ''
            if e['addresses']['is_enabled'] and e['addresses']['main_address']:
                addr = e['addresses']['main_address']
                e['location'] = ', '.join([addr['title'], addr['address'], addr['city']['title']])
                if addr['metro_station']: e['location'] = '{}, м. {}'.format(e['location'], addr['metro_station']['name'])

            if not e['screen_name']: e['screen_name'] = 'event{}'.format(e['id'])
            e['description'] = "<a href='https://vk.com/{}' title = 'vk_id: {}'>{}</a><br/>{}".format(e['screen_name'], e['id'], e['name'], e['location'])

            if not 'finish_date' in e:
                d = 24 * 60 * 60
                e['finish_date'] = (e['start_date'] + d) // d * d - 60 - self.timezone * 60 * 60

            e['colorId'] = color_scheme.get(args.colors[0], 0) if e['member_status'] == self.definitely_id else color_scheme.get(args.colors[1], 0)

        print('verbose vk events: {}'.format(self.events))
        return len(self.events)


# time format converters =======================================================

def isofromtimestamp(timestamp: int) -> str:
    return datetime.datetime.fromtimestamp(timestamp, tz = datetime.timezone.utc).isoformat()

def timestampfromiso(iso: str) -> int:
    # return datetime.datetime.fromisoformat(iso) not supported for python 3.5.3
    iso = iso[:-3] + '00'
    d = datetime.datetime.strptime(iso, '%Y-%m-%dT%H:%M:%S%z')
    return d.timestamp()

# google calendar ==============================================================

# pip install google-api-python-client==1.7.9 google-auth==1.23.0 google-auth-oauthlib==0.4.1 google-auth-httplib2
# adapted fo python v3.5.3

import googleapiclient
from google.oauth2 import service_account
from googleapiclient.discovery import build

class google_calendar:
    scope = 'https://www.googleapis.com/auth/calendar'

    colorId = { # see https://lukeboyle.com/blog/posts/google-calendar-api-color-id
        'Default'  :  0, # color of calendar
        'Lavender' :  1, #7986cb
        'Sage'     :  2, #33b679
        'Grape'    :  3, #8e24aa
        'Flamingo' :  4, #e67c73
        'Banana'   :  5, #f6c026
        'Tangerine':  6, #f5511d
        'Peacock'  :  7, #039be5
        'Graphite' :  8, #616161
        'Blueberry':  9, #3f51b5
        'Basil'    : 10, #0b8043
        'Tomato'   : 11, #d60000
    }

    def __init__(self, auth_file: str, calendar_id: str):
        credentials = service_account.Credentials.from_service_account_file(auth_file, scopes = [self.scope])
        self.__service = googleapiclient.discovery.build('calendar', 'v3', credentials = credentials)
    
        # get calendar info
        calendar_list = self.__service.calendarList().list().execute()
        calendar_list = [i for i in calendar_list['items'] if i['id'] == calendar_id]
        if len(calendar_list) < 1:
            # insert calendar (first time function)
            calendar_list_entry = {'id': calendar_id}
            created_calendar_list_entry = self.__service.calendarList().insert(body = calendar_list_entry).execute()
            print(created_calendar_list_entry['summary'])

            calendar_list = self.__service.calendarList().list().execute()
            calendar_list = [i for i in calendar_list['items'] if i['id'] == calendar_id]
    
        if len(calendar_list) < 1:
            exit(-1)

        print('calendar info: {}'.format(calendar_list[0]))

        self.__calendar_id = calendar_id
        self.__calendar = calendar_list[0]

    def get_events(self, time: int = 0):
        events_result = self.__service.events().list(calendarId = self.__calendar_id, timeMin = isofromtimestamp(time), singleEvents = True).execute()
        self.events = events_result.get('items', [])

        print('calendar events list: {}'.format(self.events))

        return len(self.events)
    
    __base_event = {
        'summary': '',
        'location': '',
        'description': '',
        'colorId': '',
        'start': {
            'dateTime': '',
            'timeZone': 'GMT',
            },
        'end': {
            'dateTime': '',
            'timeZone': 'GMT',
            },
    }

    def __event_upd(self, vk_event, g_event = __base_event):
        g_event['summary'] = vk_event['name']
        if vk_event['location'] not in g_event['location']:
            g_event['location'] = vk_event['location']
        if vk_event['description'] not in g_event['description']:
            g_event['description'] = vk_event['description']
        g_event['start']['dateTime'] = isofromtimestamp(vk_event['start_date'])
        g_event['end']['dateTime'] = isofromtimestamp(vk_event['finish_date'])
        g_event['colorId'] = vk_event['colorId']

        if 'id' in g_event:
            event_result = self.__service.events().update(calendarId = self.__calendar_id, eventId = g_event['id'], body = g_event).execute()
            print ('Event updated: {}'.format(event_result.get('htmlLink')))
        else:
            event_result = self.__service.events().insert(calendarId = self.__calendar_id, body = g_event).execute()
            print ('Event insert: {}'.format(event_result.get('htmlLink')))

    def __event_del(self, event_id: int):
        event_result = self.__service.events().delete(calendarId = calendar.__calendar_id, eventId = event_id).execute()
        print ('Event delete: {}'.format(event_id))

    def events_upd(self, vk_events: list, force: bool = False):
        # edit events list
        for e in [i for i in self.events if 'vk_id: ' in i['description']]: # is robots event
            if not 'location' in e: e['location'] = ''
            for ve in vk_events:
                if 'vk_id: {}'.format(ve['id']) in e['description']:
                    if force or\
                       ve['name'] != e['summary'] or \
                       ve['location'] not in e['location'] or \
                       ve['description'] not in e['description'] or \
                       ve['start_date'] != timestampfromiso(e['start']['dateTime']) or \
                       ve['finish_date'] != timestampfromiso(e['end']['dateTime']) or \
                       ('colorId' not in e and ve['colorId'] != self.colorId['Default']) or \
                       ('colorId' in e and ve['colorId'] != int(e['colorId'])) or \
                       False:
                        self.__event_upd(ve, e)

                    ve['id'] = 0
                    break
            else:
                self.__event_del(e['id'])

        for ve in [i for i in vk_events if i['id'] != 0]:
            self.__event_upd(ve)

# main function ================================================================
if __name__ == "__main__":
    from argparse import ArgumentParser, FileType
    import datetime

    print('command line parsing ==============================================')

    parser = ArgumentParser(prog='vk events', description='VK events to Google calenar')
    parser.add_argument('-v', '--vk-token'   , dest = 'vk', required=True, type = FileType(), metavar='<file name>', help='VK user token. see https://oauth.vk.com/authorize?client_id=2685278&scope=offline&redirect_uri=https://api.vk.com/blank.html&response_type=token')
    parser.add_argument('-g', '--google-auth', dest = 'ga', required=True, type = str, metavar='<file name>', help='Google API authentification file')
    parser.add_argument('-c', '--calendar-id', dest = 'cid', required=True, type = FileType(), metavar='<file name>', help='Calendar id for insert')
    parser.add_argument('-f', '--force'      , dest = 'force_upd', action='store_true', help='Force update all items')
    parser.add_argument('--colors', dest = 'colors', nargs='+', default=['Default', 'Tangerine'], metavar='<definitely color> [possibly color]', help='definitely and possibly events colors. Variants: {}'.format(', '.join(['"{}"'.format(i) for i in google_calendar.colorId.keys()])))

    args = parser.parse_args()
    if len(args.colors) < 2: args.colors.append(args.colors[0])

    curr_time = datetime.datetime.utcnow().timestamp()

    print('vk events download ================================================')

    vk_events = vk(args.vk.read())
    vk_events.events_verbose(google_calendar.colorId, curr_time)

    # google calendar ==========================================================

    print('google calendar events download ===================================')

    calendar = google_calendar(args.ga, args.cid.read())
    calendar.get_events(curr_time)

    print('sync events =======================================================')

    calendar.events_upd(vk_events.events, args.force_upd)

    print('success ===========================================================')
