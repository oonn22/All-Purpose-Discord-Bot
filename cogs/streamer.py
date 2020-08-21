from discord.ext import commands
from Classes.twitch_streamer import TwitchStreamer
from Classes.database import Database


class Streamer(commands.Cog):

    def __init__(self, db: Database):
        self.db = db

    @commands.group()
    @commands.has_permissions(administrator=True)
    async def streamer(self, ctx):
        if 'add' not in ctx.message.content and 'remove' not in \
                ctx.message.content and 'view' not in ctx.message.content:
            await ctx.send(
                'Use:\n;streamer add <streamer name>- adds a streamer to'
                ' get notifications for\n;streamer remove '
                '<streamer name> - removes notifications for a '
                'streamer\n;streamer view - shows all streamers that '
                'notifications are set for.')

    @streamer.command(name='add')
    async def add_streamer(self, ctx, *, streamer_login: str):
        stream = TwitchStreamer(streamer_login)

        if await stream.validate_user():
            await self.db.add_new_streamer(str(ctx.guild.id), streamer_login)
            await ctx.send('Successfully added streamer!')
        else:
            await ctx.send('Can\'t find streamer, check spelling!')

    @streamer.command(name='remove')
    async def remove_streamer(self, ctx, *, streamer_login: str):
        if streamer_login in await self.db.get_streamers(str(ctx.guild.id)):
            await self.db.remove_streamer(str(ctx.guild.id), streamer_login)
            await ctx.send('Removed streamer!')
        else:
            await ctx.send('Can\'t find streamer, check spelling!')

    @streamer.command(name='view')
    async def view_streamers(self, ctx):
        streamers = await self.db.get_streamers(str(ctx.guild.id))
        msg = 'Streamers notified for:\n```\n'

        for streamer in streamers:
            msg += streamer + '\n'
        msg += '```'

        await ctx.send(msg)
