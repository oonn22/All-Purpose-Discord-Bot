import discord
from discord.ext import commands
from discord_database import DiscordDatabase
from weather import Weather
from typing import Optional
from random import randint

bot = commands.Bot(command_prefix=';',
                   case_insensitive=True,
                   help_command=None
                   )
db = DiscordDatabase(host='SQL_HOST_HERE',
                     user='SQL_USER_HERE',
                     passwd='SQL_PASSWORDHERE'
                     )
w = Weather('OPENWEATHERAPI_KEY_HERE')


# ---EVENTS---------------------------------------------------------------------


@bot.event
async def on_ready():
    """ Code here is run on initial successful connection with discord
    """
    print('Successfully connected with discord!')

    act = discord.Activity(name=';help for commands!',
                           type=discord.ActivityType.playing)
    await bot.change_presence(activity=act)


@bot.event
async def on_guild_join(guild):
    """executes when a new guild is joined. creates tables for the
    new server and populates a default announcement channel.
    """

    print('joined server: ' + str(guild) + ', ID: ' + str(guild.id))

    if guild.system_channel:
        announce_channel = guild.system_channel
    else:
        find_gen = discord.utils.find(lambda chnl: 'general' in
                                                   str(chnl).lower(),
                                      guild.text_channels)

        if find_gen:  # found a text channel containing general in its name
            announce_channel = find_gen
        else:  # no general channel found using 1st text channel in guild
            announce_channel = guild.text_channels[0]

    db.on_join_guild(str(guild.id), str(announce_channel.id))

    await announce_channel.send('Thanks for inviting me to your server! I will'
                                ' be using this as a default channel for '
                                'announcements, if you would like to change '
                                'that use command: \n '
                                ';announcement <channel name>')


@bot.event
async def on_message(message):
    """ executes whenever a message is sent in any server.
    """
    if message.author.bot:
        return  # prevents other bots from using ours

    await bot.process_commands(message)
    # check if a command was invoked, after running this function's code


@bot.event
async def on_command_error(ctx, error):
    """ handling for errors occurring when commands are called
    """

    if isinstance(error, commands.errors.CheckFailure):
        # handling for when a check fails
        await ctx.channel.send(ctx.author.mention + ' You do not have '
                               'permission to do that or you\'re banned! '
                               'Contact an admin for assistance.')
    elif isinstance(error, commands.BadArgument):
        # bad arguments past to a command
        await ctx.channel.send('Invalid arguments!')
    else:
        # An error occurred in the command
        await ctx.channel.send('There is an error in your command!')
        print(error, type(error))


# ---CHECKS---------------------------------------------------------------------


@bot.check
async def is_blocked(ctx) -> bool:
    """ check to see if user id is in blocked database. is a global check that
    verifies on every command.
    """
    return not db.is_banned(str(ctx.author.id), str(ctx.guild.id))
    # checks pass on a True value, so need the not to make unbanned users pass


# ---COMMANDS-------------------------------------------------------------------


@bot.command(name='help')
async def help_cmd(ctx):
    """ sends all commands with descriptions
    """
    desc = ctx.author.mention + ' Here are my commands!\n\n' \
           'General Commands: \n' \
           ';roll [amount] d[sides] - Rolls :amount: of :sides: sided dice.\n'\
           ';weather - Gives a current forecast for this servers set region.\n'

    if commands.has_permissions(administrator=True):
        desc += '\n Admin Only Commands: \n' \
                ';area [city], [state], [country] - sets the guilds weather ' \
                    'region. All parameters are optional except city.\n' \
                ';announce [msg] - sends [msg] to the announcement ' \
                    'channel, tagging everyone. \n' \
                ';announcement [channel] - changes which channel ' \
                    'announcements are sent to. \n' \
                ';block [user] - prevents [user] from using commands.\n' \
                ';unblock [user] - allows [user] to use commands again.'

    await ctx.channel.send(desc)


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


@bot.command(name='weather')
async def weather(ctx):
    """ Sends the current weather of the guilds area in the channel command was
    used.
    """
    location = db.get_weather_area(str(ctx.guild.id))

    if location is None or location == 'NULL':
        await ctx.channel.send('No location set, use ;area to set one!')
    else:
        weather_report = 'Weather for ' + location.title() + '\n' + \
                         w.get_report(location)
        await ctx.channel.send(weather_report)


@bot.command(name='area')
@commands.has_permissions(administrator=True)
async def area(ctx, *,  city_region: str):
    """ Sets region to provide weather updates for. Announcements
    will appear in default text channel, unless otherwise specified with
    ;announcement command. Admins only.
    """
    if w.is_valid_location(city_region):
        db.update_weather_region(city_region, str(ctx.guild.id))
        await ctx.channel.send('Weather area is now set to: ' + city_region)
    else:
        await ctx.channel.send('Area: ' + city_region + ' is Invalid!')


@bot.command(name='announcement')
@commands.has_permissions(administrator=True)
async def announcement(ctx, *, chnl: Optional[discord.TextChannel] = None):
    """ Sets text channel in which announcements from the bot will be posted in.
    Admins only.
    """
    if chnl:
        db.update_announcement_chnl(str(chnl.id), str(ctx.guild.id))
        await ctx.channel.send('Announcements will now be posted in ' +
                               chnl.mention)
    else:
        chnl_searched = ctx.message.content[14:]
        await ctx.channel.send('Could not find channel: ' + chnl_searched + '!')


@bot.command(name='announce')
@commands.has_permissions(administrator=True)
async def announce(ctx, *, msg: str):
    """ sends msg to the guilds announcement channel, tagging everyone.
    """
    if msg:
        chnl = bot.get_channel(db.get_announcment_chnl(str(ctx.guild.id)))
        await chnl.send(ctx.author.mention + ' Says: \n' + msg +
                        '\n' + str(ctx.guild.default_role))


@bot.command(name='block')
@commands.has_permissions(administrator=True)
async def block(ctx, *, member: Optional[discord.Member] = None):
    """ Admin only command. prevents :user: from accessing bot commands in the
    guild the command is called in.
    """
    if member:
        if db.block_user(str(member.id), str(ctx.guild.id)):
            # user is not banned
            await ctx.channel.send('User ' + member.mention + ' was banned!')
        else:  # user already banned
            await ctx.channel.send('User ' + member.mention +
                                   ' already banned!')
    else:
        user_searched = ctx.message.content[7:]
        await ctx.channel.send('Couldn\'t find user: ' + user_searched + '\n' +
                               'Make sure you are using the correct '
                               'capitalization, or you can try mentioning them!'
                               )


@bot.command(name='unblock')
@commands.has_permissions(administrator=True)
async def unblock(ctx, *, member: Optional[discord.Member] = None):
    """ Admin only command. Allows :user: to use bot commands again in the guild
    the command is called in.
    """
    if member:
        if db.unblock_user(str(member.id), str(ctx.guild.id)):
            await ctx.channel.send('User ' + member.mention + ' was unbanned!')

        else:
            await ctx.channel.send('User ' + member.mention + ' is not banned!')
    else:
        user_searched = ctx.message.content[9:]
        await ctx.channel.send('Couldn\'t find user: ' + user_searched + '\n' +
                               'Make sure you are using the correct '
                               'capitalization, or you can try mentioning them!'
                               )

bot.run('INSERT_TOKEN_HERE')
