# -*- coding: utf-8 -*-

import vk_api

app_id = 2685278 # KateMobile

if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser(prog='vk event', description='VK events to Google calenar')
    parser.add_argument('-t', '--token', required=True, type=str, metavar='<token>', help='VK user token. see https://oauth.vk.com/authorize?client_id=2685278&scope=2199023255551&redirect_uri=https://api.vk.com/blank.html&display=page&response_type=token&revoke=1')
    args = parser.parse_args()

    vk_session = vk_api.VkApi(login = ' ', token = args.token, app_id = app_id)
    vk_session.auth(token_only = True)

    vk = vk_session.get_api()

    responce = vk.users.get()

    print(responce)
