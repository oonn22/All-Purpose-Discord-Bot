import discord
from discord.ext import commands
from Classes.database import ServerManageDatabase
from typing import Optional


class Announce(commands.Cog):

    def __init__(self, db: ServerManageDatabase):
        self.db = db

    @commands.group()
    @commands.has_permissions(administrator=True)
    async def announce(self, ctx, *,
                       chnl: Optional[discord.TextChannel] = None):
        if chnl is not None:
            await self.db.set_announcement_channel(str(ctx.guild.id),
                                                   str(chnl.id))
            await ctx.send(ctx.author.mention + ' set channel ' + chnl.mention +
                           ' for announcements!')
        else:
            print(ctx.message.content)
            if 'here' not in ctx.message.content and \
                    'view' not in ctx.message.content:
                await ctx.send('Use: \n;announce here - sets this channel for '
                               'announcements \n;announce <#channel> - sets '
                               '<#channel> as the announcement channel \n;announce '
                               'view - see what channel is the announcement '
                               'channel.')

    @announce.command(name='here')
    async def announce_here(self, ctx):
        await self.db.set_announcement_channel(str(ctx.guild.id),
                                               str(ctx.channel.id))
        await ctx.send(ctx.author.mention +
                       ' set this channel for announcements!')

    @announce.command(name='view')
    async def announce_view(self, ctx):
        a_chnl = await self.db.get_announcement_chnl(str(ctx.guild.id))
        await ctx.send('The announcement channel is: ' +
                       ctx.guild.get_channel(int(a_chnl)).mention)
