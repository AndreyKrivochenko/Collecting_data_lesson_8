import re
from copy import deepcopy
from urllib.parse import urlencode

import scrapy
from scrapy.http import HtmlResponse

from instaparser.items import InstaparserItem


class InstagramcomSpider(scrapy.Spider):
    name = 'InstagramCom'
    allowed_domains = ['instagram.com']
    start_urls = ['https://www.instagram.com/']
    inst_login_link = 'https://www.instagram.com/accounts/login/ajax/'
    username = 'Onliskill_udm'
    enc_password = '#PWD_INSTAGRAM_BROWSER:10:1644677079:AX1QAFsfSNcVaV94ohcAQgPEbgInWVmdhDQtD3X4Mn3b5aFlf0DLvP8n0h4wptBszm9uImjjVyUqeS3THd6sK8aR1KwvCr7OiR7vfHLATExBtX1+YcoCXNVoCA48Xjf9J2L7N4/hewUPutX/rQGS'
    user_parse = ['alt_drama', 'muzkom22']
    friends_url = 'https://i.instagram.com/api/v1/friendships'

    def parse(self, response: HtmlResponse):
        csrf = self.get_csrf(response)
        yield scrapy.FormRequest(
            self.inst_login_link,
            method='POST',
            callback=self.login,
            formdata={
                'username': self.username,
                'enc_password': self.enc_password
            },
            headers={
                'x-csrftoken': csrf
            }
        )

    def login(self, response: HtmlResponse):
        j_data = response.json()
        if j_data['authenticated']:
            for user in self.user_parse:
                yield response.follow(
                    f'/{user}/',
                    callback=self.user_data_parse,
                    cb_kwargs={'username': user}
                )

    def user_data_parse(self, response: HtmlResponse, username):
        user_id = self.get_user_id(response, username)
        variables_followers = {
            'count': 12,
            'search_surface': 'follow_list_page'
        }
        variables_following = {
            'count': 12
        }
        url_followers = f'{self.friends_url}/{user_id}/followers/?{urlencode(variables_followers)}'
        url_following = f'{self.friends_url}/{user_id}/following/?{urlencode(variables_following)}'
        yield response.follow(
            url_followers,
            callback=self.user_followers_pars,
            cb_kwargs={
                'username': username,
                'user_id': user_id,
                'variables_followers': deepcopy(variables_followers)
            },
            headers={
                'User-Agent': 'Instagram 155.0.0.37.107'
            }
        )
        yield response.follow(
            url_following,
            callback=self.user_following_pars,
            cb_kwargs={
                'username': username,
                'user_id': user_id,
                'variables_following': deepcopy(variables_following)
            },
            headers={
                'User-Agent': 'Instagram 155.0.0.37.107'
            }
        )

    def user_followers_pars(self, response: HtmlResponse, username, user_id, variables_followers):
        j_data = response.json()
        if j_data.get('big_list'):
            variables_followers['max_id'] = j_data.get('next_max_id')
            url_followers = f'{self.friends_url}/{user_id}/followers/?{urlencode(variables_followers)}'
            yield response.follow(
                url_followers,
                callback=self.user_followers_pars,
                cb_kwargs={
                    'username': username,
                    'user_id': user_id,
                    'variables_followers': deepcopy(variables_followers)
                },
                headers={
                    'User-Agent': 'Instagram 155.0.0.37.107'
                }
            )

        users = j_data.get('users')
        for user in users:
            item = InstaparserItem(
                _id=user.get('pk'),
                from_user=username,
                type='followers',
                username=user.get('username'),
                full_name=user.get('full_name'),
                profile_pic_url=user.get('profile_pic_url')
            )
            yield item

    def user_following_pars(self, response: HtmlResponse, username, user_id, variables_following):
        j_data = response.json()
        if j_data.get('big_list'):
            variables_following['max_id'] = j_data.get('next_max_id')
            url_following = f'{self.friends_url}/{user_id}/following/?{urlencode(variables_following)}'
            yield response.follow(
                url_following,
                callback=self.user_following_pars,
                cb_kwargs={
                    'username': username,
                    'user_id': user_id,
                    'variables_following': deepcopy(variables_following)
                },
                headers={
                    'User-Agent': 'Instagram 155.0.0.37.107'
                }
            )

        users = j_data.get('users')
        for user in users:
            item = InstaparserItem(
                _id=user.get('pk'),
                from_user=username,
                type='following',
                username=user.get('username'),
                full_name=user.get('full_name'),
                profile_pic_url=user.get('profile_pic_url')
            )
            yield item

    @staticmethod
    def get_csrf(response: HtmlResponse):
        text = response.text
        match = re.search("\"csrf_token\":\"\\w+\"", text).group()
        result = match.split(':').pop().strip('"')
        return result

    @staticmethod
    def get_user_id(response: HtmlResponse, username):
        text = response.text
        match = re.search("\{\"id\":\"\\d+\",\"username\":\"" + f"{username}" + "\"\}", text).group()
        result = match.split(',')[0].split(':').pop().strip('"')
        return result
