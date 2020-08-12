import aiohttp
from datetime import datetime


class Weather:
    """ Uses OpenWeatherMapAPI to provide weather details about a location.

    === Public Attributes ===

    === Private Attributes ===
    _query_url: url for querying weather api

    === Representation Invariants ===

    """
    _query_url: str

    def __init__(self, api_key: str):
        self._query_url = 'http://api.openweathermap.org/data/2.5/' \
                          'forecast?id=524901&APPID=' + api_key

    async def get_report(self, location: str) -> str:
        url = self._query_url + '&q=' + location

        if await self.is_valid_location(location):
            async with aiohttp.ClientSession() as session:
                async with session.get(url=url) as resp:
                    weather_info = await resp.json()
                    current_weather = weather_info['list'][00]
                    report = 'Report Generated for: '

                    timestamp = current_weather['dt'] + weather_info['city'][
                        'timezone']
                    actual_tmp = self._k_to_celsius(
                        current_weather['main']['temp'])
                    felt_tmp = self._k_to_celsius(
                        current_weather['main']['feels_like'])
                    condition = current_weather['weather'][0]['main'] + ', ' + \
                                current_weather['weather'][0]['description']

                    report += str(datetime.utcfromtimestamp(timestamp)) + \
                              ' Local time.\n'
                    report += 'Weather: ' + condition + '\n'
                    report += 'Actual Temperature: ' + str(
                        actual_tmp) + '°C\n' + \
                              'Feels Like: ' + str(felt_tmp) + '°C'

                    return report

    async def is_valid_location(self, location: str) -> bool:
        """return if api query returned valid response
        """
        url = self._query_url + '&q=' + location

        async with aiohttp.ClientSession() as session:
            async with session.get(url=url) as resp:
                return resp.status == 200

    def _k_to_celsius(self, kelvin: float) -> float:
        """ converts kelvin temps to celsius, rounds to 1 decimal.
        """
        return round(kelvin - 273.15, 1)
