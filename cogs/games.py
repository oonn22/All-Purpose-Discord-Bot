from time import time
from asyncio import sleep
from discord.ext import commands
from Classes.database import Database
from random import randint, choice
from typing import Optional


class Games(commands.Cog):
    db = None  # to use with or check, will figure out a better way to do this

    def __init__(self, db: Database):
        self.db = db
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
              ";beg - beg for a chance to recieve some credits.\n" \
              "\n**Slots**\n" \
              ";slots <bet> - roll the slot machine and win credits based off " \
              "your bet!\n" \
              ";scoring - see how the scoring system works\n" \
              "\n**Blackjack**\n" \
              "To Be Implemented\n" \
              "\n**Adventure**\n" \
              "Coming Soon!"
        await ctx.send(msg)

    @commands.command(name='credits')
    @commands.check(check_player_has_account)
    async def credits(self, ctx):
        creds = await self.db.get_player_credits(str(ctx.author.id))
        await ctx.send(ctx.author.mention + ' you have: ' +
                       str(creds) + ' Credits!')

    @commands.command(name='daily')
    @commands.check(check_player_has_account)
    async def daily(self, ctx):
        last_daily = await self.db.get_player_daily(str(ctx.author.id))
        now = int(time())
        time_dif = now - last_daily

        if time_dif >= 86400:
            await self.gained_credits(ctx,
                                      str(ctx.author.id),
                                      randint(5, 25),
                                      self.db
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
        if randint(0, 100) == 69:
            await self.gained_credits(ctx,
                                      str(ctx.author.id),
                                      randint(1, 5),
                                      self.db
                                      )
        else:
            await ctx.send("No credits for you!")

    @staticmethod
    async def gained_credits(ctx, player_id: str, amount: int, db: Database):
        await ctx.send(ctx.author.mention + ' Congratulations! '
                                            'you have gained: ' +
                       str(amount) + ' Credits!')
        await db.add_player_credits(player_id, amount)

    @staticmethod
    async def lost_credits(ctx, player_id: str, amount: int, db: Database):
        await ctx.send(ctx.author.mention + ' you have lost: ' +
                       str(amount) + ' Credits! Better luck next time!')
        await db.add_player_credits(player_id, -1 * amount)


class Slots(commands.Cog):

    emojis = (':alien:', ':peach:', ':gun:',
              ':b:', ':seven:', ':eagle:', ':vhs:')
    scoring_dict = {':alien:': 3, ':peach:': 2.5, ':gun:': 1.5,
               ':b:': 5, ':seven:': 7, ':eagle:': 2, ':vhs:': 0.5}

    def __init__(self, db: Database):
        self.db = db

    @commands.command(name='slots')
    @commands.check(Games.check_player_has_account)
    async def slots(self, ctx, *, bet: Optional[int] = -1):
        if bet > 0:
            player = str(ctx.author.id)
            if await self.db.get_player_credits(player) < bet:
                await ctx.send("Not enough credits to place bet!")
            else:
                roll = Slots._gen_roll()
                result = Slots._determine_win(roll)
                await Slots._send_roll(ctx, roll)

                if 0 < result < 1:
                    amount_lost = bet - bet * result
                    await Games.lost_credits(ctx, player, amount_lost, self.db)
                elif result < 1:
                    amount_lost = -1 * bet * result
                    await Games.lost_credits(ctx, player, amount_lost, self.db)
                else:
                    amount_won = bet * result
                    await Games.gained_credits(ctx, player, amount_won, self.db)
        else:
            await ctx.send("Please enter a valid bet!")

    @commands.command(name='scoring')
    async def scoring(self, ctx):
        msg = "**Get 3 of any symbol in a row and win!** " \
              "The values for each symbol are: \n"
        for key in Slots.scoring_dict.keys():
            msg += key + " bet *x" + str(Slots.scoring_dict[key]) + '*\n'
        await ctx.send(msg)

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
            roll.append(choice(Slots.emojis))
        return roll

    @staticmethod
    def _determine_win(roll: list) -> int:
        result = -1
        # check horizontal and vertical
        for i in range(0, 9, 3):
            if roll[i] == roll[i+1] and roll[i+1] == roll[i+2]:
                if Slots.scoring[roll[i]] > result:
                    result = Slots.scoring[roll[i]]
            j = i // 3
            print(j + 3, j + 6)
            if roll[j] == roll[j+3] and roll[j+3] == roll[j+6]:
                if Slots.scoring[roll[j]] > result:
                    result = Slots.scoring[roll[j]]
        # check diagonal
        if roll[1] == roll[4] and roll[4] == roll[8]:
            if Slots.scoring[roll[4]] > result:
                result = Slots.scoring[roll[4]]
        if roll[2] == roll[4] and roll[4] == roll[6]:
            if Slots.scoring[roll[4]] > result:
                result = Slots.scoring[roll[4]]

        return result


class Blackjack:
    pass
