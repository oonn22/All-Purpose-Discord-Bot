import discord_helpers as discord_helpers
from discord.ext import commands
from Classes.twitch_streamer import TwitchStreamer
from Classes.database import StreamerDatabase


class Twitch(commands.Cog):

    def __init__(self, db: StreamerDatabase):
        self.db = db

    @commands.group()
    @commands.has_permissions(administrator=True)
    async def twitch(self, ctx):
        if 'add' not in ctx.message.content and 'remove' not in \
                ctx.message.content and 'view' not in ctx.message.content:
            await ctx.send(
                'Use:\n'
                ';twitch add <streamer name> - adds a streamer to'
                ' get notifications for\n'
                ';twitch remove <streamer name> - removes notifications for a '
                'streamer\n'
                ';twitch view - shows all streamers that '
                'notifications are set for.')

    @twitch.command(name='add')
    async def add_streamer(self, ctx, *, streamer_login: str):
        stream = TwitchStreamer(streamer_login)
        res = None
        if await stream.validate_user():
            await self.db.add_new_streamer(str(ctx.guild.id), streamer_login)
            res = await ctx.send('Successfully added streamer!')
        else:
            res = await ctx.send('Can\'t find streamer, check spelling!')
        await discord_helpers.del_msgs_after([ctx.message, res], delay_until_del=10)

    @twitch.command(name='remove')
    async def remove_streamer(self, ctx, *, streamer_login: str):
        res = None
        if streamer_login in await self.db.get_streamers(str(ctx.guild.id)):
            await self.db.remove_streamer(str(ctx.guild.id), streamer_login)
            res = await ctx.send('Removed streamer!')
        else:
            res = await ctx.send('Can\'t find streamer, check spelling!')
        await discord_helpers.del_msgs_after([ctx.message, res], delay_until_del=10)

    @twitch.command(name='view')
    async def view_streamers(self, ctx):
        await ctx.message.delete()
        streamers = await self.db.get_streamers(str(ctx.guild.id))
        msg = 'Streamers notified for:\n```\n'

        for streamer in streamers:
            msg += streamer + '\n'
        msg += '```'

        await ctx.send(msg)
