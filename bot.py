import discord
import config
import Classes.database as database
import discord_helpers as discord_helpers
from discord.ext import commands, tasks
from cogs import twitch, announce, manage_users, games
from Classes.weather import Weather
from Classes.exceptions import BlockedCommandError
from Classes.check_live import CheckLive
from random import randint

bot = commands.Bot(command_prefix=';',
                   case_insensitive=True,
                   help_command=None
                   )
management_db = database.ServerManageDatabase()
streamer_db = database.StreamerDatabase()
games_db = database.GamesDatabase()
w = Weather(config.open_weather_api_key)
live_check = CheckLive(streamer_db, management_db)

# ---Events---------------------------------------------------------------------


@bot.event
async def on_ready():
    print("connected to discord")
    await management_db.initialize()
    await streamer_db.initialize()
    await games_db.initialize()
    await management_db.check_new_guilds(bot.guilds)

    act = discord.Activity(name='twitch.tv/l337_WTD',
                           type=discord.ActivityType.watching)
    await bot.change_presence(activity=act)
    await is_live.start()


@bot.event
async def on_guild_join(guild):
    await management_db.add_new_guild(guild)


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
        res = await ctx.send(ctx.author.mention + ' You do not have permission to do that! '
                                                  'Contact an admin for assistance.')
        await discord_helpers.del_msgs_after([ctx.message, res])
        print(error)
    elif isinstance(error, BlockedCommandError):
        res = await ctx.send(ctx.author.mention + ' You are banned! Ask an admin to revoke it!')
        await discord_helpers.del_msgs_after([ctx.message, res])
    elif isinstance(error, games.NotInGameError):
        res = await ctx.send(ctx.author.mention + ' please start a game first! Use **;games** to view game commands!')
        await discord_helpers.del_msgs_after([ctx.message, res], delay_until_del=10)
    elif isinstance(error, commands.BadArgument):
        # bad arguments past to a command
        res = await ctx.send('Invalid arguments! Your command most likely isn\'t structured properly')
        await discord_helpers.del_msgs_after([ctx.message, res])
    else:
        await ctx.channel.send('There is an error in your command!')
        print(error, type(error))

# ---CHECKS---------------------------------------------------------------------


@bot.check
async def is_blocked(ctx) -> bool:
    """ check to see if user id is in blocked database. is a global check that
    verifies on every command.
    """
    if await management_db.is_banned(str(ctx.author.id), str(ctx.guild.id)):
        raise BlockedCommandException
    else:
        return True

# ---COMMANDS-------------------------------------------------------------------


@bot.command(name='help')
async def help(ctx):
    help_msg = "Here are my commands:\n" \
               "\n**Admin Commands:**\n" \
               ";twitch - Gives more info on commands related to twitch " \
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
    response = await ctx.channel.send('Bot is online!')
    await discord_helpers.del_msgs_after([ctx.message, response], delay_until_del=10)


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

# ---TASKS----------------------------------------------------------------------
@tasks.loop(minutes=1.5)
async def is_live():
    await live_check.check_live(bot)

# ---COGS-----------------------------------------------------------------------
bot.add_cog(twitch.Twitch(streamer_db))
bot.add_cog(announce.Announce(management_db))
bot.add_cog(manage_users.ManageUsers(management_db))
bot.add_cog(games.Games(games_db))
bot.add_cog(games.SlotMachine())
bot.add_cog(games.Blackjack(bot))

# ------------------------------------------------------------------------------

bot.run(config.bot_token)
# https://discord.com/api/oauth2/authorize?client_id=735617826894774363&permissions=8&scope=bot
