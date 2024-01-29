# -*- coding: utf-8 -*-

import requests
import time

app_id = 2685278 # KateMobile

if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser(prog='vk event', description='VK events to Google calenar')
    parser.add_argument('-t', '--token', required=True, type=str, metavar='<token>', help='VK user token. see https://oauth.vk.com/authorize?client_id=2685278&scope=offline&redirect_uri=https://api.vk.com/blank.html&response_type=token')
    args = parser.parse_args()

    data = {'access_token': args.token, 'v': '5.199'}
 
    response = requests.post('https://api.vk.com/method/users.get', data = data)
    if not response: exit(-1)
    print(response.json())
    user_id = response.json()['response'][0]['id']

    data['user_id'] = user_id
    data['filter'] = 'events'
    data['extended'] = 1
    data['fields'] = 'start_date,finish_date,addresses'
    response = requests.post('https://api.vk.com/method/groups.get', data = data)
    if not response: exit(-1)
    events = [{k: v for k, v in i.items() if not 'photo' in k} for i in response.json()['response']['items'] if i['start_date'] > time.time() - 2 * 60 * 60]
    print(events)
