import vk_api
from config import acces_token
from vk_api.exceptions import ApiError
from datetime import datetime
from pprint import pprint
from random import randint

from operator import itemgetter

class VkTools:
    def __init__(self, acces_token):
        self.vkapi = vk_api.VkApi(token=acces_token)

    def _bdate_toyear(self, bdate):
        if bdate != None:
            user_year = bdate.split('.')[2]
            now = datetime.now().year
            age = now - int(user_year)
        else:
            age = None
        return age


    def get_profile_info(self, user_id):
        try:
            info, = self.vkapi.method('users.get',
                                      {'user_id': user_id,
                                       'fields': 'city, sex, relation, bdate'
                                      }
                                     )
        except ApiError as e:
            info = {}
            print(f'error = {e}')

        result = {'name': (info['first_name']) #+ ' ' + info['last_name']
                  if 'first_name' in info and 'last_name' in info else None,
                  'sex': info.get('sex') if 'sex' in info else None,
                  'city': info.get('city')['title'] if info.get('city') is not None else None,
                  'bdate': info['bdate'] if 'bdate' in info else None,
                  'year': self._bdate_toyear(info.get('bdate'))

        }

        return result

    def search_worksheet(self, params, offset):
        try:
            users = self.vkapi.method('users.search',
                                      {'count': 50,
                                       'offset': offset,
                                       'hometown': params['city'],
                                       'sex': 1 if params['sex'] == 2 else 2,
                                       'has_photo': True,
                                       'age_from': params['year'] - 3,
                                       'age_to': params['year'] + 3
                                      }
                                     )
        except ApiError as e:
            users = []
            print(f'error = {e}')

        result = [{
            'name': item['first_name'] + ' ' +item['last_name'],
            'id': item['id']
                    } for item in users['items'] if item['is_closed'] is False
                    ]

        return result

    def get_photos(self, id):
        try:
            photos = self.vkapi.method('photos.get',
                                      {'owner_id': id,
                                       'album_id': 'profile',
                                       'extended': 1
                                      }
                                     )
        except ApiError as e:
            photos = {}
            print(f'error = {e}')

        result = [{'owner_id': item['owner_id'],
                   'id': item['id'],
                   'likes': item['likes']['count'],
                   'comments': item['comments']['count']
                   } for item in photos['items']
                  ]

        '''сортировка по лайкам и коментам'''
        for i in range(len(result)):
            result = sorted(result, key=itemgetter('likes', 'comments'), reverse=True)

        return result[:3]




if __name__ == '__main__':
    user_id = '588055212'
    tools = VkTools(acces_token)
    params = tools.get_profile_info(user_id)
    worksheets = tools.search_worksheet(params, 20)
    worksheet = worksheets.pop()
    photos = tools.get_photos(worksheet['id'])
    pprint(params)
