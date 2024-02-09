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
    tz = int(response.json()['response'][0]['timezone']) * 60 * 60

    data['user_id'] = user_id
    data['filter'] = 'events'
    data['extended'] = 1
    data['fields'] = 'start_date,finish_date,addresses'
    response = requests.post('https://api.vk.com/method/groups.get', data = data)
    if not response: exit(-1)
    events = [{k: v for k, v in i.items() if not 'photo' in k} for i in response.json()['response']['items'] if i['start_date'] >= time]
    for event in events:
        if not 'finish_date' in event:
            d = 24 * 60 * 60
            event['finish_date'] = (event['start_date'] + d) // d * d - 60 - tz

        event['start_date']  -= tz
        event['finish_date'] -= tz
    print(events)

    return events


if __name__ == "__main__":
    from argparse import ArgumentParser, FileType
    import datetime

    parser = ArgumentParser(prog='vk events', description='VK events to Google calenar')
    parser.add_argument('-v', '--vk-token', dest = 'vk', required=True, type = FileType(), metavar='<vk-token>', help='VK user token. see https://oauth.vk.com/authorize?client_id=2685278&scope=offline&redirect_uri=https://api.vk.com/blank.html&response_type=token')
    parser.add_argument('-g', '--google-auth', dest = 'ga', required=True, type = str, metavar='<google-auth>', help='Google API authentification file')
    parser.add_argument('-c', '--calendar-id', dest = 'cid', required=True, type = str, metavar='<calendar-id>', help='Calendar id for insert')
    args = parser.parse_args()

    curr_time = datetime.datetime.utcnow()

    vk_events = vk_get_events(args.vk.read(), curr_time.timestamp())
    for e in vk_events:
        e['location'] = ''
        if e['addresses']['is_enabled'] and e['addresses']['main_address']:
            addr = e['addresses']['main_address']
            e['location'] = f"{addr['title']}, {addr['address']}, {addr['city']['title']}"
            if addr['metro_station']: e['location'] = f"{e['location']}, м. {addr['metro_station']['name']}"

        if not e['screen_name']: e['screen_name'] = f"event{e['id']}"
        e['description'] = f"<a href='https://vk.com/{e['screen_name']}' title = 'vk_id: {e['id']}'>{e['name']}</a><br/>{e['location']}"

    # google calendar ==========================================================

    # pip install --upgrade google-api-python-client
    # pip install --upgrade google-auth google-auth-oauthlib google-auth-httplib2

    import googleapiclient
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    g_auth = args.ga

    credentials = service_account.Credentials.from_service_account_file(g_auth, scopes = [g_scope])
    service = googleapiclient.discovery.build('calendar', 'v3', credentials = credentials)

    # get calendar info
    calendar_list = service.calendarList().list().execute()
    calendar_list = [i for i in calendar_list['items'] if i['id'] == args.cid]
    if len(calendar_list) < 1:
        # insert calendar (first time function)
        calendar_list_entry = {'id': args.cid}
        created_calendar_list_entry = service.calendarList().insert(body=calendar_list_entry).execute()
        print(created_calendar_list_entry['summary'])
    
        calendar_list = service.calendarList().list().execute()
        calendar_list = [i for i in calendar_list['items'] if i['id'] == args.cid]
    
    if len(calendar_list) < 1:
        exit(-1)

    print(calendar_list[0])

    # get events list
    events_result = service.events().list(calendarId = args.cid, timeMin = curr_time.isoformat() + 'Z', singleEvents = True).execute()
    events = events_result.get('items', [])
    print(events)

    # edit events list
    for event in [i for i in events if 'vk_id: ' in i['description']]: # is robots event
        if not 'location' in event: event['location'] = ''
        for vk_event in vk_events:
            if f"vk_id: {vk_event['id']}" in event['description']:
                s = int(datetime.datetime.fromisoformat(event['start']['dateTime']).timestamp())
                f = int(datetime.datetime.fromisoformat(event['end']['dateTime']).timestamp())
                # todo: timezone hardcode !!!
                if vk_event['name'] != event['summary'] or \
                   vk_event['location'] != event['location'] or \
                   vk_event['description'] not in event['description'] or \
                   vk_event['start_date'] != s - 3 * 60 * 60 or \
                   vk_event['finish_date'] != f - 3 * 60 * 60 or \
                   False:
                    
                    event['summary'] = vk_event['name']
                    event['location'] = vk_event['location']
                    if vk_event['description'] not in event['description']:
                        event['description'] = vk_event['description']
                    event['start']['dateTime'] = datetime.datetime.fromtimestamp(vk_event['start_date']).isoformat() + 'Z'
                    event['end']['dateTime'] = datetime.datetime.fromtimestamp(vk_event['finish_date']).isoformat() + 'Z'
                    
                    # update event
                    updated_event = service.events().update(calendarId = args.cid, eventId = event['id'], body = event).execute()
                    print (updated_event['updated'])  # Print the updated date.

                vk_event['id'] = 0
                break
        else:
            # delete event
            service.events().delete(calendarId = args.cid, eventId = event['id']).execute()
            print(f"event '{event['id']}' is deleted")

    for vk_event in [i for i in vk_events if i['id'] != 0]:
        event = {
            'summary': vk_event['name'],
            'location': vk_event['location'],
            'description': vk_event['description'],
            'start': {
                'dateTime': datetime.datetime.fromtimestamp(vk_event['start_date']).isoformat() + 'Z',
                },
            'end': {
                'dateTime': datetime.datetime.fromtimestamp(vk_event['finish_date']).isoformat() + 'Z',
                },
            }
        
        # add new event
        event_result = service.events().insert(calendarId = args.cid, body = event).execute()
        print ('Event created: %s' % (event_result.get('htmlLink')))
