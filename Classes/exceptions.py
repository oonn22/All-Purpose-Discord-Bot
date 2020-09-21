from discord.ext.commands import CommandError


class Error401Exception(Exception):
    pass


class BlockedCommandError(CommandError):
    pass


class NotInGameError(CommandError):
    pass


class TwitchAuthorizationError(Exception):

    def __init__(self):
        super().__init__("Error with Oauth authorization, "
                         "Check twitch credentials!")
