# -*- coding: utf-8 -*-

app_id = 2685278 # KateMobile
g_scope = 'https://www.googleapis.com/auth/calendar'

# vkontakte ====================================================================
def vk_get_events(vk_token: str, time: int):

    import requests

    data = {'access_token': vk_token, 'v': '5.199', 'fields': 'timezone'}

    response = requests.post('https://api.vk.com/method/users.get', data = data)
    if not response: exit(-1)
    print(response.json())
    user_id = response.json()['response'][0]['id']
    timezone = int(response.json()['response'][0]['timezone'])

    data['user_id'] = user_id
    data['filter'] = 'events'
    data['extended'] = 1
    data['fields'] = 'start_date,finish_date,addresses'
    response = requests.post('https://api.vk.com/method/groups.get', data = data)
    if not response: exit(-1)

    events = [{k: v for k, v in i.items() if not 'photo' in k} for i in response.json()['response']['items'] if i['start_date'] >= time]
    print(events)

    return events, timezone

def isofromtimestamp(timestamp: int) -> str:
    return datetime.datetime.fromtimestamp(timestamp, tz = datetime.timezone.utc).isoformat()

def timestampfromiso(iso: str) -> int:
    # return datetime.datetime.fromisoformat(iso) not supported for python 3.5.3
    iso = iso[:-3] + '00'
    d = datetime.datetime.strptime(iso, '%Y-%m-%dT%H:%M:%S%z')
    return d.timestamp()

if __name__ == "__main__":
    from argparse import ArgumentParser, FileType
    import datetime

    parser = ArgumentParser(prog='vk events', description='VK events to Google calenar')
    parser.add_argument('-v', '--vk-token', dest = 'vk', required=True, type = FileType(), metavar='<vk-token>', help='VK user token. see https://oauth.vk.com/authorize?client_id=2685278&scope=offline&redirect_uri=https://api.vk.com/blank.html&response_type=token')
    parser.add_argument('-g', '--google-auth', dest = 'ga', required=True, type = str, metavar='<google-auth>', help='Google API authentification file')
    parser.add_argument('-c', '--calendar-id', dest = 'cid', required=True, type = FileType(), metavar='<calendar-id>', help='Calendar id for insert')
    args = parser.parse_args()

    curr_time = datetime.datetime.utcnow()

    vk_events, timezone = vk_get_events(args.vk.read(), curr_time.timestamp())
    for e in vk_events:
        e['location'] = ''
        if e['addresses']['is_enabled'] and e['addresses']['main_address']:
            addr = e['addresses']['main_address']
            e['location'] = ', '.join([addr['title'], addr['address'], addr['city']['title']])
            if addr['metro_station']: e['location'] = '{}, м. {}'.format(e['location'], addr['metro_station']['name'])

        if not e['screen_name']: e['screen_name'] = 'event{}'.format(e['id'])
        e['description'] = "<a href='https://vk.com/{}' title = 'vk_id: {}'>{}</a><br/>{}".format(e['screen_name'], e['id'], e['name'], e['location'])

        if not 'finish_date' in e:
            d = 24 * 60 * 60
            e['finish_date'] = (e['start_date'] + d) // d * d - 60 - timezone * 60 * 60

    # google calendar ==========================================================

    # pip install google-api-python-client==1.7.9
    # pip install google-auth==1.23.0 google-auth-oauthlib==0.4.1 google-auth-httplib2
    # adapted fo python v3.5.3

    import googleapiclient
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    g_auth = args.ga

    g_calendar_id = args.cid.read()

    credentials = service_account.Credentials.from_service_account_file(g_auth, scopes = [g_scope])
    service = googleapiclient.discovery.build('calendar', 'v3', credentials = credentials)

    # get calendar info
    calendar_list = service.calendarList().list().execute()
    calendar_list = [i for i in calendar_list['items'] if i['id'] == g_calendar_id]
    if len(calendar_list) < 1:
        # insert calendar (first time function)
        calendar_list_entry = {'id': g_calendar_id}
        created_calendar_list_entry = service.calendarList().insert(body=calendar_list_entry).execute()
        print(created_calendar_list_entry['summary'])
    
        calendar_list = service.calendarList().list().execute()
        calendar_list = [i for i in calendar_list['items'] if i['id'] == g_calendar_id]
    
    if len(calendar_list) < 1:
        exit(-1)

    print(calendar_list[0])

    # get events list
    events_result = service.events().list(calendarId = g_calendar_id, timeMin = curr_time.isoformat() + 'Z', singleEvents = True).execute()
    events = events_result.get('items', [])
    print(events)

    # edit events list
    for event in [i for i in events if 'vk_id: ' in i['description']]: # is robots event
        if not 'location' in event: event['location'] = ''
        for vk_event in vk_events:
            if 'vk_id: {}'.format(vk_event['id']) in event['description']:
                if vk_event['name'] != event['summary'] or \
                   vk_event['location'] != event['location'] or \
                   vk_event['description'] not in event['description'] or \
                   vk_event['start_date'] != timestampfromiso(event['start']['dateTime']) or \
                   vk_event['finish_date'] != timestampfromiso(event['end']['dateTime']) or \
                   False:
                    
                    event['summary'] = vk_event['name']
                    event['location'] = vk_event['location']
                    if vk_event['description'] not in event['description']:
                        event['description'] = vk_event['description']
                    event['start']['dateTime'] = isofromtimestamp(vk_event['start_date'])
                    event['end']['dateTime'] = isofromtimestamp(vk_event['finish_date'])
                    
                    # update event
                    updated_event = service.events().update(calendarId = g_calendar_id, eventId = event['id'], body = event).execute()
                    print (updated_event['updated'])  # Print the updated date.

                vk_event['id'] = 0
                break
        else:
            # delete event
            service.events().delete(calendarId = g_calendar_id, eventId = event['id']).execute()
            print('event "{}" is deleted'.format(event['id']))

    for vk_event in [i for i in vk_events if i['id'] != 0]:
        event = {
            'summary': vk_event['name'],
            'location': vk_event['location'],
            'description': vk_event['description'],
            'start': {
                'dateTime': isofromtimestamp(vk_event['start_date']),
                'timeZone': 'GMT',
                },
            'end': {
                'dateTime': isofromtimestamp(vk_event['finish_date']),
                'timeZone': 'GMT',
                },
            }
        
        # add new event
        event_result = service.events().insert(calendarId = g_calendar_id, body = event).execute()
        print ('Event created: %s' % (event_result.get('htmlLink')))
