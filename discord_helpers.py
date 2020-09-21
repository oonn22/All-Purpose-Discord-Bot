import discord
import re
import asyncio


async def del_msgs_after(msgs: list, delay_until_del=5):
    await asyncio.sleep(delay_until_del)
    for msg in msgs:
        await msg.delete()


def markdownify_message(msg: str) -> str:
    """removes accidental discord markdown characters from a
    string by adding  \\ to them.
    """
    to_return = ''
    split_with_link = re.split(r'(http\S+)', msg)
    split_no_link = re.split(r'http\S+', msg)
    for item in split_with_link:
        if item in split_no_link:
            last = 0
            for match in re.finditer('[_*~]', item):
                to_return += item[last:match.start()] + '\\'
                last = match.start()
            to_return = to_return + item[last:]
        else:
            to_return += item
    return to_return


if __name__ == '__main__':
    print(markdownify_message('@everyone unsympathisch_tv has gone live! check them out at https://www.twitch.tv/unsympathisch_tv\nTitle: Among Us mit paar Kollegen\nGame: Among Us\nViewers: 6225'))




