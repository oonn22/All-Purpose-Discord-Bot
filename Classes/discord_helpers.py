import discord
import asyncio


async def del_msgs_after(msgs: list, delay_until_del=5):
    await asyncio.sleep(delay_until_del)
    for msg in msgs:
        await msg.delete()


