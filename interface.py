import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
from core import VkTools
from config import *
from data_store import *

vk = vk_api.VkApi(token=comunity_token)

# send message
class BotInterface():
    def __init__(self, comunity_token, acces_token):
        self.vk = vk_api.VkApi(token=comunity_token)
        self.longpoll = VkLongPoll(self.vk)
        self.vk_tools = VkTools(acces_token)
        self.params = {}
        self.worksheets = []
        self.offset = 0
        self.check_result = []


    def message_send(self, user_id, message, attachment=None):
        self.vk.method('messages.send',
                  {'user_id': user_id,
                   'message': message,
                   'attachment': attachment,
                   'random_id': get_random_id()}
                   )

    ''' photo{owner_id}_{id}'''
    def worksheet_photos(self, worksheet):
        photos = self.vk_tools.get_photos(worksheet['id'])
        photo_string = ''
        for photo in photos:
            photo_string += f'photo{photo["owner_id"]}_{photo["id"]},'
        return photo_string

    def black_list(self, key):
        result = {}
        param = {'name': 'ФИО',
                 'sex': 'Пол',
                 'city': 'Город',
                 'bdate': 'Дата рождения',
                 'year': 'Возраст'
                 }
        for k, v in param.items():
            if k == key:
                result[key] = param[k]
        return result

# event handling
    def event_hendler(self):
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                if event.text.lower() == 'привет':
                    '''логика получения данных о пользователе'''
                    self.params = self.vk_tools.get_profile_info(event.user_id)

                    for k, v in self.params.items():
                        if v is None:
                            result = (self.black_list(k)[k])
                            self.check_result.append(result)

                    if not self.check_result:
                        self.message_send(
                            event.user_id,
                            f'Привет, {self.params["name"]}!\n'
                            f'Вас приветствует бот VKinder!\n'
                            f'Бот осуществляет поиск подходящей по критериям пары.\n'
                            f'Чтобы начать/продолжить поиск введите команду "поиск".\n'
                            f'Для завершения работы команду "пока".\n'
                        )

                    else:
                        self.message_send(
                            event.user_id,
                            f'Привет, {self.params["name"]}!\n'
                            f'Вас приветствует бот VKinder!\n'
                            f'В вашем профиле не заполнено: {self.check_result}.\n'
                            f'Чтобы продолжить работу отредактируйте данные профиля"\n'
                            f'и наберите команду "привет".\n'
                        )

                elif event.text.lower() == 'поиск' and not self.check_result:
                    '''логика для поиска анкет'''
                    self.message_send(
                        event.user_id, 'Начинаем поиск')
                    flag = False
                    try:
                        while flag == False:
                            if self.worksheets:
                                worksheet = self.worksheets.pop()
                                photo_string = self.worksheet_photos(worksheet)
                            else:
                                try:
                                    self.worksheets = self.vk_tools.search_worksheet(
                                        self.params, self.offset)
                                    worksheet = self.worksheets.pop()
                                    photo_string = self.worksheet_photos(worksheet)
                                except AttributeError as e:
                                    print(f'error = {e}')

                            try:
                                '''проверка анкеты в бд в соответствие с event.user_id'''
                                result = check_user(engine, event.user_id, worksheet['id'])
                            except UnboundLocalError as e:
                                print(f'error = {e}')

                            if result == False:
                                flag = True

                            if not self.worksheets:
                                self.offset += 100
                    except TypeError as e:
                        print(f'error = {e}')

                    self.message_send(
                        event.user_id,
                        f'имя: {worksheet["name"]} ссылка: vk.com/{worksheet["id"]}',
                        attachment=photo_string
                        )

                    '''добавить анкету в бд в соответствие с event.user_id'''
                    add_user(engine, event.user_id, worksheet['id'])

                elif event.text.lower() == 'пока':
                    self.message_send(event.user_id, 'До новых встреч')

                elif event.text.lower() == 'поиск' and self.check_result:
                    self.message_send(event.user_id, 'Пожалуйста, заполните профиль.')

                else:
                    self.message_send(event.user_id, 'Неизвестная команда')



if __name__ == '__main__':
    bot_interface = BotInterface(comunity_token, acces_token)
    bot_interface.event_hendler()
