import aiomysql
from typing import List, Optional

"""
Tables we have: 
gid_announcement - one column Announcement_ID, stores 1 value a channel id
gid_streamers - two column Streamer_login, stores streamer names for a server
gid_banned - stores user ids of banned users

"""


class Database:
    """

    """

    def __init__(self):
        self._db = _DatabaseInteraction()

    async def initialize(self, host: str, port: int,  user: str, passwd: str):
        await self._db.connect(host, port, user, passwd)
        await self._db.execute('CREATE DATABASE IF NOT EXISTS discordtwitch;')
        await self._db.execute('USE discordtwitch;')

    async def check_new_guilds(self, guilds: list):
        """ Check if any guilds were added while bot was offline, and creates
        tables for guilds that added the bot.
        """
        tables = await self._db.execute('show tables;', return_results=True)

        for g in guilds:
            is_new = True
            gid = str(g.id)
            for table in tables:
                if gid in table[0]:
                    is_new = False
                    break
            if is_new:
                await self.add_new_guild(g)

    async def add_new_guild(self, guild):
        """ Creates tables for :guild:
        """
        gid = str(guild.id)
        await self._db.create_table('g' + gid + '_announcement',
                                    ['Announcement_ID VARCHAR(255)'])
        await self._db.create_table('g' + gid + '_streamers',
                                    ['Streamer_login VARCHAR(255)'])
        await self._db.create_table('g' + gid + '_bannedusers',
                                    ['User_ID BIGINT'])

        await self.set_announcement_channel(gid,
                                            self._get_default_announce_chnl(guild))

    async def add_new_streamer(self, guild_id: str, streamer_login: str):
        """ Adds streamer_login to the streamer table corresponding to
        :guild_id:
        """
        await self._db.insert('g' + guild_id + '_streamers',
                              ['Streamer_login', ],
                              ['\'' + streamer_login + '\''])

    async def remove_streamer(self, guild_id: str, streamer_login: str):
        """ Removes streamer_login from the streamer table corresponding to
        :guild_id:
        """
        await self._db.delete('g' + guild_id + '_streamers',
                              'Streamer_login = \'' + streamer_login + '\'')

    async def get_streamers(self, guild_id: str) -> list:
        """ return list of all streamers in streamer table corresponding to
        :guild_id:
        """
        streams = await self._db.get_value('g' + guild_id + '_streamers',
                                     ['Streamer_login'])
        streamers = []
        for item in streams:
            streamers.append(item[0])
        return streamers

    async def get_announcement_chnl(self, guild_id: str) -> str:
        chnl_id = await self._db.get_value('g' + guild_id + '_announcement',
                                           ['Announcement_ID'])
        return chnl_id[0][0]

    async def set_announcement_channel(self, guild_id, announcement_chnl_id):
        guild_table = 'g' + guild_id + '_announcement'
        to_replace = await self._db.get_value(guild_table, ['Announcement_ID'])

        if to_replace:
            await self._db.update(guild_table, ['Announcement_ID'],
                                  [announcement_chnl_id],
                                  'Announcement_ID = ' + str(to_replace[0][0]))
        else:
            await self._db.insert(guild_table, ['Announcement_ID'],
                                  [announcement_chnl_id])

    def _get_default_announce_chnl(self, guild) -> str:
        if guild.system_channel:
            announce_channel = guild.system_channel
        else:
            found_gen = None
            for chnl in guild.text_channels:
                if 'general' in str(chnl).lower():
                    found_gen = chnl
                    break

            if found_gen:  # found a text channel containing general in its name
                announce_channel = found_gen
            else:  # no general channel found using 1st text channel in guild
                announce_channel = guild.text_channels[0]

        return str(announce_channel.id)

    async def block_user(self, user_id: str, guild_id: str) -> bool:
        """ return whether user_id was successfully blocked in :guild_id:
        """
        if await self.is_banned(user_id, guild_id):
            # user in table, cant ban.
            return False
        else:
            guild_banned_table = 'g' + guild_id + '_bannedusers'
            await self._db.insert(guild_banned_table, ['User_ID'], [user_id])
            return True

    async def unblock_user(self, user_id: str, guild_id: str) -> bool:
        """ return whether :user_id: was successfully unblocked in :guild_id:
        """
        if await self.is_banned(user_id, guild_id):
            guild_banned_table = 'g' + guild_id + '_bannedusers'
            await self._db.delete(guild_banned_table, 'User_ID = ' + user_id)
            return True
        else:  # user in table, cant ban.
            return False

    async def get_banned_user_ids(self, guild_id: str) -> list:
        """ return list of all members id in bannedusers table corresponding to
        :guild_id:
        """
        ids = await self._db.get_value('g' + guild_id + '_bannedusers',
                                       ['User_ID'])
        member_ids = []
        for item in ids:
            member_ids.append(item[0])
        return member_ids

    async def is_banned(self, user_id: str, guild_id: str) -> bool:
        """ return whether :user_id: is banned in :guild_id:
        """
        guild_banned_table = 'g' + guild_id + '_BannedUsers'
        return await self._db.in_table(guild_banned_table, 'User_ID', user_id)


class _DatabaseInteraction:
    """ Class to query and send commands to a MySQl server.

    === Public Attributes ===

    === Private Attributes ===
    _db: points to our MySQL server
    _cursor: used to execute MySQL commands

    === Representation Invariants ===

    """
    _db: aiomysql

    async def connect(self, host: str, port: int, user: str, passwd: str):
        """ creates a MySQL instance by connecting to a server with the given
        credentials, and assigns us a way to interact with our server.
        """
        self._db = await aiomysql.connect(
            host=host,
            port=port,
            user=user,
            password=passwd,
            autocommit=True
        )

    async def execute(self, cmd: str, return_results=False) -> Optional[List[tuple]]:
        """ Executes cmd on MySQL server. returns results if :return_results:.
        """
        async with await self._db.cursor() as cur:
            await cur.execute(cmd)
            result = await cur.fetchall() if return_results else None
            await cur.close()
        return result

    async def create_table(self, table_name: str,
                     columns_name_type: List[str]) -> None:
        """ will create a table with name :table: if it doesnt already exist.
        assigns columns form :columns_name_type: to the new table.
        precondition: values in :columns_name_type: must follow correct MySQL
        syntax where there is a column name followed by a data type for it.
        """
        command = 'CREATE TABLE IF NOT EXISTS ' + table_name + '('
        for item in columns_name_type:
            command += item + ', '
        command = command[:-2] + ');'

        await self.execute(command)

    async def in_table(self,  table: str, row: str, to_find: str) -> bool:
        """ return whether :to_find: is in :row: of :table:.
        """
        op = ' = '
        if to_find == 'NULL':
            op = ' IS '

        return bool(await self.execute('SELECT ' + row + ' FROM ' + table +
                                       ' WHERE ' + row + op + to_find + ';',
                                       True))
        # execute returns a list, if list is empty know not in table so false

    async def get_value(self, table: str, columns: List[str]) -> List[tuple]:
        """ query and return values from :table: under :column:
        """
        command = 'SELECT '
        for item in columns:
            command += item + ', '
        command = command[:-2] + ' FROM ' + table + ';'

        return await self.execute(command, return_results=True)

    async def insert(self,  table: str, columns: List[str], items: List[str]) -> None:
        """ insert items into :table: where elements from :items: go to the
        column with the same index in :columns:.
        precondition: len(items) == len(columns)
        """
        command = 'INSERT INTO ' + table + ' ('

        for item in columns:
            command += item + ', '

        command = command[:-2] + ') VALUES ('

        for item in items:
            command += item + ', '

        command = command[:-2] + ');'
        await self.execute(command)

    async def update(self, table: str, columns: List[str], values: [str],
                     update_condition: str) -> None:
        """ updates the columns in :columns: from :table:, with the elements of
        :values: of the same index, if :update_condition: is met.
        precondition: len(columns) == len(values) and update_condition is
        correct MySQL syntax (column = value)
        """
        command = 'UPDATE ' + table + ' SET '

        for i in range(len(columns)):
            command += columns[i] + ' = ' + values[i] + ', '

        command = command[:-2] + ' WHERE ' + update_condition + ';'
        await self.execute(command)

    async def delete(self, table: str, delete_condition: str):
        """ deletes values from :table: where :delete_condition: is met
        precondition: :delete_condition: is proper MySQL syntax
        """
        command = 'DELETE FROM ' + table + ' WHERE ' + delete_condition + ';'
        await self.execute(command)


