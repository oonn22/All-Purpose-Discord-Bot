import Classes.discord_helpers as discord_helpers
from time import time
from asyncio import sleep
from discord.ext import commands
from Classes.database import GamesDatabase
from Classes.blackjack_game import BlackjackGame
from random import randint, choice
from typing import Optional


class Games(commands.Cog):
    db = None  # used staticly in this class for static checks

    def __init__(self, db: GamesDatabase):
        Games.db = db

    async def check_player_has_account(ctx) -> bool:
        if not await Games.db.player_exists(str(ctx.author.id)):
            await Games.db.create_player(str(ctx.author.id))
            await ctx.author.send("An account has been created for you! You "
                                  "have 10 credits and your daily will reset "
                                  "in 24 hours. If you run out of credits you "
                                  "can try begging.")
        return True

    @commands.command(name='games')
    async def games(self, ctx):
        msg = "Here is the available game commands I have:\n" \
              "\n**General**:\n" \
              ";credits - See how many credits you have.\n" \
              ";daily - claim your daily allowance.\n" \
              ";beg - beg for a chance to receive some credits.\n" \
              ";leaderboard - show who's dominating the server.\n" \
              "\n**Slot Machine**\n" \
              ";slots <bet> - roll the slot machine and win credits based off " \
              "your bet!\n" \
              ";scoring - see how the scoring system works\n" \
              "\n**Blackjack**\n" \
              ";deal <bet> - deals your hand and starts the game.\n" \
              ";hit - add another card to your hand\n" \
              ";stand - end your turn\n" \
              "\n**Adventure**\n" \
              "Coming Soon!"
        await ctx.send(msg)

    @commands.command(name='credits')
    @commands.check(check_player_has_account)
    async def credits(self, ctx):
        await ctx.message.delete()
        creds = await Games.db.get_player_credits(str(ctx.author.id))
        await ctx.send(ctx.author.mention + ' you have: ' +
                       str(creds) + ' Credits!')

    @commands.command(name='daily')
    @commands.check(check_player_has_account)
    async def daily(self, ctx):
        await ctx.message.delete()
        last_daily = await Games.db.get_player_daily(str(ctx.author.id))
        now = int(time())
        time_dif = now - last_daily
        player = str(ctx.author.id)

        if time_dif >= 86400:
            await Games.db.update_player_daily(player)
            await self.gained_credits(ctx,
                                      player,
                                      randint(5, 25),
                                      Games.db
                                      )
        else:
            hours = (86400 - time_dif) // 3600
            mins = ((86400 - time_dif) - (hours * 3600)) // 60
            await ctx.send(ctx.author.mention + ' you have ' +
                           str(hours) + ' hours and ' + str(mins) +
                           ' minutes until your next daily!')

    @commands.command(name='beg')
    @commands.check(check_player_has_account)
    async def beg(self, ctx):
        rand = randint(5, 70)
        if rand == 69:
            await ctx.message.delete()
            await self.gained_credits(ctx,
                                      str(ctx.author.id),
                                      randint(1, 5),
                                      Games.db
                                      )
        elif rand == 68:
            await ctx.message.delete()
            await self.lost_credits(ctx,
                                    str(ctx.author.id),
                                    1,
                                    Games.db
                                    )
        else:
            res = await ctx.send("No credits for you!")
            await discord_helpers.del_msgs_after([ctx.message, res])

    @commands.command(name='leaderboard')
    async def leaderboard(self, ctx):
        await ctx.message.delete()
        users_in_guild = []
        msg = "The top players in this server are:\n"
        for user in ctx.guild.members:
            if await Games.db.player_exists(str(user.id)):
                creds = await Games.db.get_player_credits(str(user.id))
                users_in_guild.append((user.name, creds))

        users_in_guild.sort(key=lambda x: x[1], reverse=True)
        users = 10
        if len(users_in_guild) < 10:
            users = len(users_in_guild)

        for i in range(1, users + 1):
            user = users_in_guild[i - 1]
            if i <= 3:
                msg += '**' + str(i) + '. ' + user[0] + ': ' + str(user[1]) + \
                       ' credits**\n'
            else:
                msg += str(i) + '. ' + user[0] + ': ' + str(user[1]) + \
                       ' credits\n'

        await ctx.send(msg)

    @staticmethod
    async def take_bet(player_id: str, bet: int, db: GamesDatabase):
        await db.add_player_credits(player_id, -bet)

    @staticmethod
    async def return_bet(player_id: str, bet: int, db: GamesDatabase):
        await db.add_player_credits(player_id, bet)

    @staticmethod
    async def gained_credits(ctx, player_id: str,
                             amount: int, db: GamesDatabase):
        await ctx.send(ctx.author.mention + ' Congratulations! '
                                            'you have gained: ' +
                       str(amount) + ' Credits!')
        await db.add_player_credits(player_id, amount)

    @staticmethod
    async def lost_credits(ctx, player_id: str, amount: int, db: GamesDatabase):
        await ctx.send(ctx.author.mention + ' you have lost: ' +
                       str(amount) + ' Credits! Better luck next time!')
        await db.add_player_credits(player_id, -1 * amount)


class SlotMachine(commands.Cog):

    emojis = (':alien:', ':peach:', ':gun:',
              ':b:', ':seven:', ':gem:')
    scoring_dict = {':alien:': 3, ':peach:': 2.5, ':gun:': 1.5,
               ':b:': 5, ':seven:': 7, ':gem:': 4}

    @commands.command(name='slots')
    @commands.check(Games.check_player_has_account)
    async def slots(self, ctx, *, bet: Optional[int] = -1):
        if bet > 0:
            player = str(ctx.author.id)
            if await Games.db.get_player_credits(player) < bet:
                await ctx.send("Not enough credits to place bet!")
            else:
                await Games.take_bet(player, bet, Games.db)
                roll = SlotMachine._gen_roll()
                result = SlotMachine._determine_win(roll)
                await SlotMachine._send_roll(ctx, roll)

                if result < 1:
                    amount_lost = bet
                    await Games.return_bet(player, int(amount_lost), Games.db)
                    await Games.lost_credits(ctx, player,
                                             int(amount_lost), Games.db)
                else:
                    amount_won = bet * result
                    await Games.gained_credits(ctx, player,
                                               int(amount_won), Games.db)
        else:
            await ctx.send("Please enter a valid bet!")

    @commands.command(name='scoring')
    async def scoring(self, ctx):
        msg = "**Get 3 of any symbol in a row and win!** " \
              "The values for each symbol are: \n"
        for key in SlotMachine.scoring_dict.keys():
            msg += key + " bet *x" + str(SlotMachine.scoring_dict[key]) + '*\n'
        res = await ctx.send(msg)
        await discord_helpers.del_msgs_after([ctx.message, res], delay_until_del=30)

    @staticmethod
    async def _send_roll(ctx, roll: [list]):
        msg = await ctx.send(ctx.author.mention + " Your roll is: ")
        await sleep(1)
        to_del = await ctx.send(roll[0] + ' ' + roll[1] + ' ' + roll[2])
        await sleep(1)
        to_del1 = await ctx.send(roll[3] + ' ' + roll[4] + ' ' + roll[5])
        await sleep(1.5)
        to_del2 = await ctx.send(roll[6] + ' ' + roll[7] + ' ' + roll[8])
        await sleep(3)
        await to_del.delete()
        await to_del1.delete()
        await to_del2.delete()
        await msg.edit(content=ctx.author.mention + " Your roll is: \n" +
                               roll[0] + ' ' + roll[1] + ' ' + roll[2] + '\n' +
                               roll[3] + ' ' + roll[4] + ' ' + roll[5] + '\n' +
                               roll[6] + ' ' + roll[7] + ' ' + roll[8])

    @staticmethod
    def _gen_roll() -> list:
        roll = []
        for i in range(9):
            roll.append(choice(SlotMachine.emojis))
        return roll

    @staticmethod
    def _determine_win(roll: list) -> int:
        result = -1
        # check horizontal and vertical
        for i in range(0, 9, 3):
            if roll[i] == roll[i+1] and roll[i+1] == roll[i+2]:
                if SlotMachine.scoring_dict[roll[i]] > result:
                    result = SlotMachine.scoring_dict[roll[i]]
            j = i // 3
            if roll[j] == roll[j+3] and roll[j+3] == roll[j+6]:
                if SlotMachine.scoring_dict[roll[j]] > result:
                    result = SlotMachine.scoring_dict[roll[j]]
        # check diagonal
        if roll[0] == roll[4] and roll[4] == roll[8]:
            if SlotMachine.scoring_dict[roll[4]] > result:
                result = SlotMachine.scoring_dict[roll[4]]
        if roll[2] == roll[4] and roll[4] == roll[6]:
            if SlotMachine.scoring_dict[roll[4]] > result:
                result = SlotMachine.scoring_dict[roll[4]]

        return result


class Blackjack(commands.Cog):
    games = {}  # struct: 'p_id': BlackjackGame

    def __init__(self, bot: commands.bot):
        self.bot = bot

    def player_in_game(ctx):
        player = str(ctx.author.id)
        if player not in Blackjack.games:
            raise NotInGameError
        return True

    @commands.command(name='deal')
    @commands.check(Games.check_player_has_account)
    async def deal(self, ctx, *, bet: Optional[int] = -1):
        if bet > 0:
            player_id = str(ctx.author.id)
            if player_id in Blackjack.games:
                await ctx.send('Player is already in a game. '
                               'Finish the other game first!')
            elif await Games.db.get_player_credits(player_id) < bet:
                await ctx.send('Not enough credits to place bet!')
            else:
                await Games.take_bet(player_id, bet, Games.db)
                msg = await ctx.send('Starting...')
                chnl_id = ctx.channel.id
                game = BlackjackGame(msg.id, chnl_id, ctx.author.mention, bet)
                Blackjack.games[player_id] = game
                await Games.update_game(game)
        else:
            await ctx.send("Please enter a valid bet!")

    @commands.command(name='hit')
    @commands.check(player_in_game)
    async def hit(self, ctx):
        game = Blackjack.games[str(ctx.author.id)]
        game.draw_player_card()
        await self.update_game(game)
        await ctx.message.delete()
        if game.dealer_turn:
            await self.dealer_turn(ctx, game)

    @commands.command(name='stand')
    @commands.check(player_in_game)
    async def stand(self, ctx):
        game = Blackjack.games[str(ctx.author.id)]
        game.player_last_action = 'stand'
        await ctx.message.delete()
        await self.update_game(game)
        await self.dealer_turn(ctx, game)

    async def dealer_turn(self, ctx, game: BlackjackGame):
        turns = game.take_dealer_turn()
        chnl = self.bot.get_channel(game.chnl_id)
        msg = await chnl.fetch_message(game.msg_id)
        for item in turns:
            await msg.edit(content=item)
            await sleep(2)
        await self.game_over(ctx, game)

    async def update_game(self, game: BlackjackGame):
        chnl = self.bot.get_channel(game.chnl_id)
        msg = await chnl.fetch_message(game.msg_id)
        await msg.edit(content=game.print_game())

    async def game_over(self, ctx, game: BlackjackGame):
        chnl = self.bot.get_channel(game.chnl_id)
        game_value = game.determine_game()
        player_id = str(ctx.author.id)
        if game_value == 0:
            await chnl.send(game.player_mention + ' you drawed! '
                                                  'Your bet has been returned')
            await Games.return_bet(player_id, game.bet, Games.db)
        elif game_value < 0:
            await Games.return_bet(player_id, game.bet, Games.db)
            await Games.lost_credits(ctx, player_id, game.bet, Games.db)
        else:
            await Games.gained_credits(ctx, player_id, game.bet * 2, Games.db)
        del Blackjack.games[player_id]


class NotInGameError(commands.CommandError):
    pass



