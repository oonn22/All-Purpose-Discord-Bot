import asyncio
from database import Database
from twitch_streamer import TwitchStreamer
from discord.ext import commands


class CheckLive:

    def __init__(self):
        self.announced_streamers = {}

    async def check_live(self, bot: commands.bot, db: Database) -> None:
        while True:
            for guild in bot.guilds:
                streamers = await db.get_streamers(str(guild.id))
                a_chnl_id = await db.get_announcement_chnl(str(guild.id))
                a_chnl = bot.get_channel(int(a_chnl_id))
                default_role = guild.default_role

                if guild.id not in self.announced_streamers:
                    self.build_dict(guild.id, streamers)

                for streamer in streamers:
                    if await self.check_streamer(TwitchStreamer(streamer),
                                                 guild.id):
                        await a_chnl.send(str(default_role) + " " + streamer
                                          + " has gone live! check them out at "
                                          "https://www.twitch.tv/" + streamer)

            await asyncio.sleep(60)

    def build_dict(self, guild_id, streamers: list):
        self.announced_streamers[guild_id] = {}
        for streamer in streamers:
            self.announced_streamers[guild_id][streamer] = False

    async def check_streamer(self, s: TwitchStreamer, guild_id) -> bool:
        is_live = await s.get_is_live()
        await asyncio.sleep(1)

        if self.announced_streamers[guild_id][s.streamer_name]:
            self.announced_streamers[guild_id][s.streamer_name] = is_live
            return False
        else:
            self.announced_streamers[guild_id][s.streamer_name] = is_live
            return is_live
