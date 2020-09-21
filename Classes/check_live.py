import asyncio
import discord_helpers
from Classes.database import StreamerDatabase, ServerManageDatabase
from Classes.twitch_streamer import TwitchStreamer
from discord.ext import commands


class CheckLive:

    def __init__(self, streamer_db: StreamerDatabase,
                 server_manage_db: ServerManageDatabase):
        self.announced_streamers = {}
        self.streamer_db = streamer_db
        self.server_manage_db = server_manage_db

    async def check_live(self, bot: commands.bot) -> None:
        for guild in bot.guilds:
            gid = str(guild.id)
            streamers = await self.streamer_db.get_streamers(gid)
            streamers = await self.build_streamers(streamers)
            a_chnl_id = await self.server_manage_db.get_announcement_chnl(gid)
            a_chnl = bot.get_channel(int(a_chnl_id))
            default_role = guild.default_role

            if guild.id not in self.announced_streamers:
                self.build_dict(guild.id, streamers)

            for streamer in streamers:
                name = streamer.streamer_name
                if name not in self.announced_streamers[guild.id]:
                    self.announced_streamers[guild.id][name] = False

                if await self.check_streamer(streamer, guild.id) and a_chnl is not None:
                    msg = str(default_role) + ' ' + name + \
                          ' has gone live! check them out at https://www.twitch.tv/'\
                          + name + '\nTitle: ' + streamer.stream_title + '\nGame: ' + \
                          streamer.stream_game + '\nViewers: ' + str(streamer.viewers)
                    msg = discord_helpers.markdownify_message(msg)
                    await a_chnl.send(msg)

    async def build_streamers(self, streamers: list) -> list:
        to_return = []
        for streamer in streamers:
            ts = TwitchStreamer(streamer)
            await ts.update_streamer_info()
            to_return.append(ts)
        return to_return

    def build_dict(self, guild_id, streamers: list):
        self.announced_streamers[guild_id] = {}
        for streamer in streamers:
            self.announced_streamers[guild_id][streamer.streamer_name] = False

    async def check_streamer(self, s: TwitchStreamer, guild_id) -> bool:
        if self.announced_streamers[guild_id][s.streamer_name]:
            self.announced_streamers[guild_id][s.streamer_name] = s.is_live
            return False
        else:
            self.announced_streamers[guild_id][s.streamer_name] = s.is_live
            return s.is_live
