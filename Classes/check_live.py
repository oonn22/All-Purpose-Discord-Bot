import asyncio
from Classes.database import Database
from Classes.twitch_streamer import TwitchStreamer
from discord.ext import commands


class CheckLive:

    def __init__(self):
        self.announced_streamers = {}

    async def check_live(self, bot: commands.bot, db: Database) -> None:
        for guild in bot.guilds:
            streamers = await db.get_streamers(str(guild.id))
            a_chnl_id = await db.get_announcement_chnl(str(guild.id))
            a_chnl = bot.get_channel(int(a_chnl_id))
            default_role = guild.default_role

            if guild.id not in self.announced_streamers:
                self.build_dict(guild.id, streamers)

            for streamer in streamers:
                if streamer not in self.announced_streamers[guild.id]:
                    self.announced_streamers[guild.id][streamer] = False

                if await self.check_streamer(TwitchStreamer(streamer),
                                             guild.id):
                    await a_chnl.send(str(default_role) + " " + streamer
                                      + " has gone live! check them out at "
                                      "https://www.twitch.tv/" + streamer)

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
