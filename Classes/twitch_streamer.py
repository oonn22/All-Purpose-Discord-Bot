import asyncio
import aiohttp
import config


class TwitchStreamer:

    def __init__(self, user: str):
        self.client_id = config.twitch_client_id
        self.client_secret = config.twitch_client_secret
        self.streamer_name = user

    async def get_is_live(self):
        url = 'https://api.twitch.tv/helix/streams?user_login=' + \
              self.streamer_name
        token = await self.get_token('')
        headers = {
            'Authorization': 'Bearer ' + token,
            'client-id': self.client_id
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url=url, headers=headers) as resp:
                json = await resp.json()
                return not json['data'] == []

    async def validate_user(self) -> bool:
        url = 'https://api.twitch.tv/helix/users?login=' + self.streamer_name
        token = await self.get_token('user:read:email')
        headers = {
            'Authorization': 'Bearer ' + token,
            'client-id': self.client_id
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url=url, headers=headers) as resp:
                json = await resp.json()
                return not json['data'] == []

    async def get_token(self, scope):
        url = 'https://id.twitch.tv/oauth2/token'
        params = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'client_credentials'
        }
        if scope != '':
            params['scope'] = scope

        async with aiohttp.ClientSession() as session:
            async with session.post(url=url, data=params) as resp:
                if resp.status == 200:
                    json = await resp.json()
                    return str(json['access_token'])


if __name__ == '__main__':
    me = TwitchStreamer('l337_WTD')
    xqc = TwitchStreamer('xQcOW')
    shroud = TwitchStreamer('shroud')
    fake = TwitchStreamer('Ahahdkcmwsjwlqamf')
    loop = asyncio.get_event_loop()
    loop.run_until_complete(fake.validate_user())
    loop.run_until_complete(xqc.validate_user())
    loop.close()
