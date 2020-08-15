import discord
import config
import traceback
from discord.ext import commands
from cogs import streamer, announce, manage_users, games
from Classes.database import Database
from Classes.weather import Weather
from Classes.blocked_command_error import BlockedCommandError
from Classes.check_live import CheckLive
from random import randint

bot = commands.Bot(command_prefix=';',
                   case_insensitive=True,
                   help_command=None
                   )
db = Database()
w = Weather(config.open_weather_api_key)

# ---Events---------------------------------------------------------------------


@bot.event
async def on_ready():
    print("connected to discord")
    await db.initialize(config.mysql_host,
                        config.mysql_port,
                        config.mysql_user,
                        config.mysql_password)
    await db.check_new_guilds(bot.guilds)

    act = discord.Activity(name='twitch.tv/l337_WTD',
                           type=discord.ActivityType.watching)
    await bot.change_presence(activity=act)


@bot.event
async def on_guild_join(guild):
    await db.add_new_guild(guild)


@bot.event
async def on_message(message):
    if message.author.bot:
        return  # prevents other bots from using ours

    await bot.process_commands(message)
    # check if a command was invoked, after running this function's code


@bot.event
async def on_command_error(ctx, error, *args, **kwargs):
    if isinstance(error, commands.errors.CheckFailure):
        # handling for when a check fails
        await ctx.send(ctx.author.mention + ' You do not have permission to do '
                                            'that! Contact an admin for '
                                            'assistance.')
        print(error)
    elif isinstance(error, BlockedCommandError):
        await ctx.send(ctx.author.mention + ' You are banned! Ask an admin to '
                                            'revoke it!')
    elif isinstance(error, games.NotInGameError):
        await ctx.send(ctx.author.mention + ' please start a game first! '
                                            'Use **;games** to view game '
                                            'commands!')
    elif isinstance(error, commands.BadArgument):
        # bad arguments past to a command
        await ctx.send('Invalid arguments! Your command most likely '
                       'isn\'t structured properly')
    else:
        # An error occurred in the command
        embed = discord.Embed(title=':x: Event Error', colour=0xe74c3c)  # Red
        embed.add_field(name='Event', value=error)
        embed.description = '```py\n%s\n```' % traceback.format_exc()
        await ctx.channel.send('There is an error in your command!')
        await ctx.channel.send(embed=embed)
        print(error, type(error))

# ---CHECKS---------------------------------------------------------------------


@bot.check
async def is_blocked(ctx) -> bool:
    """ check to see if user id is in blocked database. is a global check that
    verifies on every command.
    """
    if await db.is_banned(str(ctx.author.id), str(ctx.guild.id)):
        raise BlockedCommandError
    else:
        return True

# ---COMMANDS-------------------------------------------------------------------


@bot.command(name='help')
async def help(ctx):
    help_msg = "Here are my commands:\n" \
               "\n**Admin Commands:**\n" \
               ";streamer - Gives more info on commands related to twitch " \
               "streamers\n" \
               ";announce - Gives more info on commands related to " \
               "announcements from this bot\n" \
               ";manageusers - Gives more info on user management commands\n" \
               "\n**General Commands:**\n" \
               ";ping - check if im online\n" \
               ";bug <mmessage> - report a bug by giving a brief description " \
               "as <message> if one is found\n" \
               ";roll <amount>d<dice_sides> - rolls <amount> of <dice_sides> " \
               "sided dice.\n" \
               ";weather <area> - gives a weather forecast for <area>\n" \
               ";games - view my commands to play games\n" \
               ";code - view my source code"
    await ctx.send(help_msg)


@bot.command(name='ping')
async def ping(ctx):
    await ctx.channel.send('Bot is online!')
    await ctx.message.delete()


@bot.command(name='roll')
async def roll(ctx, *, dice: str):
    """returns the rolls of :amount: d:sides: dice.
    """
    dice = dice.split('d')

    try:
        amount = int(dice[0])
        sides = int(dice[1])
    except ValueError:
        raise commands.BadArgument

    if amount > 0 and sides > 0:
        results = 'Results: '
        total = 0
        for i in range(amount):
            r = randint(1, sides)
            results += str(r) + ', '
            total += r

        if len(results) >= 2000:
            await ctx.channel.send('Total: ' + str(total))
        else:
            await ctx.channel.send(results[:-2] + '\nTotal: ' + str(total))
    else:
        raise commands.BadArgument


@bot.command(name='bug')
async def bug(ctx, *, msg: str):
    """reports a bug to the creator.
    """
    creator = bot.get_user(int(config.discord_creator_id))
    await creator.send(msg + '\nfrom: ' + ctx.author.mention)
    await ctx.message.delete()


@bot.command(name='weather')
async def weather(ctx, *, location: str):
    if await w.is_valid_location(location):
        await ctx.send(await w.get_report(location))


@bot.command(name='code')
async def code(ctx):
    await ctx.send('View my code at: '
                   'https://github.com/oonn22/All-Purpose-Discord-Bot')


# ---METHODS--------------------------------------------------------------------

# ---COGS-----------------------------------------------------------------------
bot.add_cog(streamer.Streamer(db))
bot.add_cog(announce.Announce(db))
bot.add_cog(manage_users.ManageUsers(bot, db))
bot.add_cog(games.Games(db))
bot.add_cog(games.Slots(db))
bot.add_cog(games.Blackjack(bot, db))

# ------------------------------------------------------------------------------
live_check = CheckLive()
bot.loop.create_task(live_check.check_live(bot, db))
bot.run(config.bot_token)
# https://discord.com/api/oauth2/authorize?client_id=735617826894774363&permissions=8&scope=bot
