import aiomysql
import asyncio
import config
from time import time
from typing import List, Optional

"""
Tables we have: 
announce_chnl - two column Guild_ID Announcement_ID, stores 2 values a guild id 
                and corresponding channel id
gid_streamers - one column Streamer_login, stores streamer names for a server
gid_banned - stores user ids of banned users
players - 3 columns Player_ID Credits Daily_Reset, stores an id number of 
          credits and unix time of last daily

"""


class _DatabaseInteraction:
    """ Class to query and send commands to a MySQl server.

    === Public Attributes ===

    === Private Attributes ===
    _pool: pool of connections to our MySQL server

    === Representation Invariants ===

    """
    _pool: aiomysql.pool


    async def initialize(self):
        """ creates a MySQL instance by connecting to a server with the given
        credentials, and assigns us a pool of ways to interact with a specified
        database on our server.
        """
        initial_conn = await aiomysql.connect(
            host=config.mysql_host,
            port=config.mysql_port,
            user=config.mysql_user,
            password=config.mysql_password,
            autocommit=True,
            loop=asyncio.get_event_loop()
        )

        async with initial_conn.cursor() as cur:
            await cur.execute('CREATE DATABASE IF NOT EXISTS ' +
                              config.mysql_database_name + ';')
        initial_conn.close()

        self._pool = await aiomysql.create_pool(
            host=config.mysql_host,
            port=config.mysql_port,
            user=config.mysql_user,
            password=config.mysql_password,
            autocommit=True,
            db=config.mysql_database_name,
            loop=asyncio.get_event_loop()
        )

    async def execute(self, cmd: str, return_results=False) -> \
            Optional[List[tuple]]:
        """ Executes cmd on MySQL server. returns results if :return_results:.
        """
        async with self._pool.acquire() as conn:
            async with conn.cursor() as cur:
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

    async def get_columns_values(self, table: str, columns: List[str]) -> \
            List[tuple]:
        """ query and return all values from :table: under :column(s):
        """
        command = 'SELECT '
        for item in columns:
            command += item + ', '
        command = command[:-2] + ' FROM ' + table + ';'

        return await self.execute(command, return_results=True)

    async def get_values(self, table: str, column: str, condition: str):
        """ query and return specific values from :table: under :column: where
        :condition: is met
        precondition: :condition: follows proper MySQL syntax
        """
        command = 'SELECT ' + column + ' FROM ' + table + ' WHERE ' + condition
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


class GamesDatabase(_DatabaseInteraction):

    def __init__(self):
        self._table_name = 'players'

    async def initialize(self):
        await super().initialize()
        await self.create_table(self._table_name,
                                ['Player_ID BIGINT',
                                 'Credits INT',
                                 'Daily_Reset BIGINT'])

    async def create_player(self, player_id: str):
        columns = ['Player_ID', 'Credits', 'Daily_Reset']
        items = [player_id, '10', str(int(time()))]
        await self.insert(self._table_name, columns, items)

    async def add_player_credits(self, player_id: str, creds: int):
        creds = await self.get_player_credits(player_id) + creds
        await self.update(self._table_name, ['Credits'], [str(creds)],
                          'Player_ID = ' + player_id)

    async def update_player_daily(self, player_id: str):
        await self.update(self._table_name, ['Daily_Reset'],
                          [str(int(time()))], 'Player_ID = ' + player_id)

    async def get_player_credits(self, player_id: str) -> int:
        creds = await self.get_values(self._table_name, 'Credits',
                                      'Player_ID = ' + player_id)
        return int(creds[0][0])

    async def get_player_daily(self, player_id: str) -> int:
        """ returns unix time of player daily column
        """
        time = await self.get_values(self._table_name, 'Daily_Reset',
                                     'Player_ID = ' + player_id)
        return int(time[0][0])

    async def player_exists(self, player_id: str) -> bool:
        return await self.in_table(self._table_name, 'Player_ID', player_id)


class StreamerDatabase(_DatabaseInteraction):

    async def add_new_streamer(self, guild_id: str, streamer_login: str):
        """ Adds streamer_login to the streamer table corresponding to
        :guild_id:
        """
        guild_table = StreamerDatabase._guild_table_name(guild_id)
        await self.insert(guild_table,
                          ['Streamer_login', ],
                          ['\'' + streamer_login + '\''])

    async def remove_streamer(self, guild_id: str, streamer_login: str):
        """ Removes streamer_login from the streamer table corresponding to
        :guild_id:
        """
        guild_table = StreamerDatabase._guild_table_name(guild_id)
        await self.delete(guild_table,
                          'Streamer_login = \'' + streamer_login + '\'')

    async def get_streamers(self, guild_id: str) -> list:
        """ return list of all streamers in streamer table corresponding to
        :guild_id:
        """
        guild_table = StreamerDatabase._guild_table_name(guild_id)
        streams = await self.get_columns_values(guild_table, ['Streamer_login'])
        streamers = []
        for item in streams:
            streamers.append(item[0])
        return streamers

    @staticmethod
    def _guild_table_name(guild_id: str) -> str:
        return 'g' + guild_id + '_streamers'


class ServerManageDatabase(_DatabaseInteraction):

    def __init__(self):
        self._announce_table_name = 'announce_chnl'

    async def initialize(self):
        await super().initialize()
        await self.create_table(self._announce_table_name,
                                ['Guild_ID BIGINT', 'Announcement_ID BIGINT'])

    async def check_new_guilds(self, guilds: list):
        """ Check if any guilds were added while bot was offline, and creates
        tables for guilds that added the bot.
        """
        tables = await self.execute('show tables;', return_results=True)

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
        await self.create_table('g' + gid + '_streamers',
                                ['Streamer_login VARCHAR(255)'])
        await self.create_table('g' + gid + '_bannedusers', ['User_ID BIGINT'])

        announce_chnl = self._get_default_announce_chnl(guild)
        await self.set_announcement_channel(gid, announce_chnl)

    async def get_announcement_chnl(self, guild_id: str) -> str:
        chnl_id = await self.get_values(self._announce_table_name,
                                        'Announcement_ID',
                                        'Guild_ID = ' + guild_id)
        return chnl_id[0][0]

    async def set_announcement_channel(self, guild_id: str,
                                       announcement_chnl_id: str):
        to_replace = await self.get_values(self._announce_table_name,
                                           'Announcement_ID',
                                           'Guild_ID = ' + guild_id)

        if to_replace:
            await self.update(self._announce_table_name,
                              ['Announcement_ID'],
                              [announcement_chnl_id],
                              'Guild_ID = ' + guild_id)
        else:
            await self.insert(self._announce_table_name,
                              ['Guild_ID', 'Announcement_ID'],
                              [guild_id, announcement_chnl_id])

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
            guild_banned_table = ServerManageDatabase._banned_table(guild_id)
            await self.insert(guild_banned_table, ['User_ID'], [user_id])
            return True

    async def unblock_user(self, user_id: str, guild_id: str) -> bool:
        """ return whether :user_id: was successfully unblocked in :guild_id:
        """
        if await self.is_banned(user_id, guild_id):
            guild_banned_table = ServerManageDatabase._banned_table(guild_id)
            await self.delete(guild_banned_table, 'User_ID = ' + user_id)
            return True
        else:  # user in table, cant ban.
            return False

    async def get_banned_user_ids(self, guild_id: str) -> list:
        """ return list of all members id in bannedusers table corresponding to
        :guild_id:
        """
        guild_banned_table = ServerManageDatabase._banned_table(guild_id)
        ids = await self.get_columns_values(guild_banned_table, ['User_ID'])
        member_ids = []
        for item in ids:
            member_ids.append(item[0])
        return member_ids

    async def is_banned(self, user_id: str, guild_id: str) -> bool:
        """ return whether :user_id: is banned in :guild_id:
        """
        guild_banned_table = ServerManageDatabase._banned_table(guild_id)
        return await self.in_table(guild_banned_table, 'User_ID', user_id)

    @staticmethod
    def _banned_table(guild_id: str) -> str:
        return 'g' + guild_id + '_bannedusers'




