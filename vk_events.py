# -*- coding: utf-8 -*-

from getpass import getpass
import vk_api

# При двухфакторной аутентификации вызывается эта функция
def auth_handler():
    key = input("Enter authentication code: ")
    # Если: True - сохранить, False - не сохранять.
    remember_device = True

    return key, remember_device

if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser(prog='vk event', description='VK events to Google calenar')

    parser.add_argument('-l', '--login', required=True, type=str, metavar='<login>', help='VK user login or email')
    parser.add_argument('-p', '--pass', dest = 'password', type=str, metavar='<password>', help='VK user password')

    args = parser.parse_args()
    if not args.password:
        args.password = getpass('input password:')
    
    try:
        vk_session = vk_api.VkApi(args.login, args.password)
    except:
        vk_session = vk_api.VkApi(args.login, args.password, auth_handler = auth_handler)
    vk_session.auth()

    vk = vk_session.get_api()

    print(vk)
