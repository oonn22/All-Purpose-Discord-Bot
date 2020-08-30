import asyncio
import aiohttp
import config
import time
from Classes.exceptions import Error401Exception, TwitchAuthorizationError


class TwitchStreamer:
    """ Represents a streamer on twitch giving useful data on their stream obtained by querying the twitch api

    === Public Attributes ===
    streamer_name: name of the streamer represented by this object
    valid: whether the streamer represented is a valid twitch user
    is_live: whether the streamer represented is currently streaming
    stream_title: if the streamer is live, this will be the title the are live under
    stream_game: if the streamer is live, this will be the game the are streaming
    viewers: if the streamer is live, this will be the number of viewers they have

    === Private Attributes ===
    _client_id: CLASS ATTRIBUTE, credential to use twitch api
    _client_secret: CLASS ATTRIBUTE, credential to create oauth token

    """
    _client_id = config.twitch_client_id
    _client_secret = config.twitch_client_secret

    def __init__(self, user: str):
        self.streamer_name = user
        self.valid = False
        self.is_live = False
        self.stream_title = ''
        self.stream_game = ''
        self.viewers = 0

    async def update_streamer_info(self):
        url = 'https://api.twitch.tv/helix/streams?user_login=' + \
              self.streamer_name
        token = await TwitchStreamer._get_token()

        if not self.valid:
            await self.validate_user()

        if self.valid:
            headers = {
                'Authorization': 'Bearer ' + token,
                'client-id': TwitchStreamer._client_id
            }
            json = await TwitchStreamer._get_request(url, headers)

            print(json, self.streamer_name)
            data = json['data']
            self.is_live = not (data == [])  # the value of 'data' for a non-live streamer is []

            if self.is_live:
                data = data[0]
                self.streamer_name = data['user_name']
                self.stream_title = data['title']
                self.stream_game = await TwitchStreamer.game_id_to_name(data['game_id'])
                self.viewers = data['viewer_count']
            else:
                self.stream_title = ''
                self.stream_game = ''
                self.viewers = 0

    async def validate_user(self) -> bool:
        url = 'https://api.twitch.tv/helix/users?login=' + self.streamer_name
        token = await TwitchStreamer._get_token(scope='user:read:email')
        headers = {
            'Authorization': 'Bearer ' + token,
            'client-id': TwitchStreamer._client_id
        }

        json = await TwitchStreamer._get_request(url, headers)
        self.valid = (not json['data'] == [])
        return self.valid

    @staticmethod
    async def game_id_to_name(game_id: str) -> str:
        url = 'https://api.twitch.tv/helix/games?id=' + game_id
        token = await TwitchStreamer._get_token()
        headers = {
            'Authorization': 'Bearer ' + token,
            'client-id': TwitchStreamer._client_id
        }

        json = await TwitchStreamer._get_request(url, headers)
        return json['data'][0]['name']

    @staticmethod
    async def _get_token(scope=''):
        url = 'https://id.twitch.tv/oauth2/token'
        params = {
            'client_id': TwitchStreamer._client_id,
            'client_secret': TwitchStreamer._client_secret,
            'grant_type': 'client_credentials'
        }
        if scope != '':
            params['scope'] = scope

        json = await TwitchStreamer._post_request(url, params)
        return json['access_token']

    @staticmethod
    async def _get_request(url, headers) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.get(url=url, headers=headers) as resp:
                json = await resp.json()
        return json

    @staticmethod
    async def _post_request(url, params) -> dict:
        json = None  # sometimes we get None as response, while loop tries again  till its a non None response
        while json is None:
            async with aiohttp.ClientSession() as session:
                async with session.post(url=url, data=params) as resp:
                    json = await resp.json()
        return json


if __name__ == '__main__':
    me = TwitchStreamer('uwumastertv')
    fake = TwitchStreamer('hjfnhejksklskfofjjjjdj903')
    offline = TwitchStreamer('ichosenn')
    loop = asyncio.get_event_loop()
    loop.run_until_complete(me.update_streamer_info())
    loop.run_until_complete(me.validate_user())
    loop.run_until_complete(fake.update_streamer_info())
    loop.run_until_complete(fake.validate_user())
    loop.run_until_complete(offline.update_streamer_info())
    loop.run_until_complete(offline.validate_user())
    loop.close()
