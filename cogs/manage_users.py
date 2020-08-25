import discord
from discord.ext import commands
from Classes.database import ServerManageDatabase
from typing import Optional


class ManageUsers(commands.Cog):

    def __init__(self, db: ServerManageDatabase):
        self.db = db

    @commands.command(name='manageusers')
    @commands.has_permissions(administrator=True)
    async def manage_users(self, ctx):
        await ctx.send('Use: \n;block <User> - Blocks <@User> from using '
                       'commands \n;unblock <@User> - allows <User> to use '
                       'commands again\n')

    @commands.command(name='block')
    @commands.has_permissions(administrator=True)
    async def block(self, ctx, *, member: Optional[discord.Member] = None):
        """ Admin only command. prevents :user: from accessing bot commands in
        the guild the command is called in.
        """
        if member:
            if await self.db.block_user(str(member.id), str(ctx.guild.id)):
                # user is not banned
                await ctx.send('User ' + member.mention + ' was banned!')
            else:  # user already banned
                await ctx.send('User ' + member.mention + ' already banned!')
        else:
            user_searched = ctx.message.content[7:]
            await ctx.send(
                'Couldn\'t find user: ' + user_searched + '\n' +
                'Make sure you are using the correct '
                'capitalization, or you can try mentioning them!'
                )

    @commands.command(name='unblock')
    @commands.has_permissions(administrator=True)
    async def unblock(self, ctx, *, member: Optional[discord.Member] = None):
        """ Admin only command. Allows :user: to use bot commands again in the
        guild the command is called in.
        """
        if member:
            if await self.db.unblock_user(str(member.id), str(ctx.guild.id)):
                await ctx.send(
                    'User ' + member.mention + ' was unbanned!')

            else:
                await ctx.send(
                    'User ' + member.mention + ' is not banned!')
        else:
            user_searched = ctx.message.content[9:]
            await ctx.send(
                'Couldn\'t find user: ' + user_searched + '\n' +
                'Make sure you are using the correct '
                'capitalization, or you can try mentioning them!'
                )

    @commands.command(name='blocked')
    async def blocked(self, ctx,):
        """ Shows all blocked members in a guild
        """
        blocked_ids = await self.db.get_banned_user_ids(str(ctx.guild.id))

        if not blocked_ids:
            await ctx.send('You have all been good! There is no banned users')
        else:
            msg = "These people have been naughty!\n"
            for user_id in blocked_ids:
                msg += self.bot.get_user(int(user_id)).mention + " \n"
            await ctx.send(msg)
