import mysql.connector
from typing import List, Optional


class DiscordDatabase:
    """ A way to create and interact with a MySQL database that will contain
    information relevant to a discord bot using pre-coded commands.

    === Public Attributes ===

    === Private Attributes ===
    _sql: interfaces with our MySQL Database

    === Representation Invariants ===

    """
    _sql: '_MySQL'  # is type _MySQL

    def __init__(self, host: str, user: str, passwd: str) -> None:
        """ Initialize a new DiscordDatabase by connecting to the MySQL server
        with the provided credentials, and creates a new database if one doesnt
        already exist.
        """
        self._sql = _MySQL(host, user, passwd)

        self._sql.execute('CREATE DATABASE IF NOT EXISTS discord;')
        self._sql.execute('USE discord;')

    def on_join_guild(self, guild_id: str, announcement_chnl_id: str) -> None:
        """ creates tables for a new guild and sets the default announcement
        channel id.
        """
        guild_info_table = 'g' + guild_id
        guild_banned_table = guild_info_table + '_BannedUsers'

        self._sql.create_table(guild_info_table,
                               ['server_weather_area VARCHAR(255)',
                                'announcement_chnl_id BIGINT NOT NULL'])
        self._sql.create_table(guild_banned_table, ['user_id BIGINT'])

        self.update_announcement_chnl(announcement_chnl_id, guild_id)

    def block_user(self, user_id: str, guild_id: str) -> bool:
        """ return whether user_id was successfully blocked in :guild_id:
        """
        if self.is_banned(user_id, guild_id):
            # user in table, cant ban.
            return False
        else:
            guild_banned_table = 'g' + guild_id + '_BannedUsers'
            self._sql.insert(guild_banned_table, ['user_id'], [user_id])
            return True

    def unblock_user(self, user_id: str, guild_id: str) -> bool:
        """ return whether :user_id: was successfully unblocked in :guild_id:
        """
        if self.is_banned(user_id, guild_id):
            guild_banned_table = 'g' + guild_id + '_BannedUsers'
            self._sql.delete(guild_banned_table, 'user_id = ' + user_id)
            return True
        else:  # user in table, cant ban.
            return False

    def is_banned(self, user_id: str, guild_id: str) -> bool:
        """ return whether :user_id: is banned in :guild_id:
        """
        guild_banned_table = 'g' + guild_id + '_BannedUsers'
        return self._sql.in_table(guild_banned_table, 'user_id', user_id)

    def get_announcment_chnl(self, guild_id: str) -> int:
        """ return :guild_id:'s announcement channel id
        """
        guild_table = 'g' + guild_id
        chnl = self._sql.get_value(guild_table, ['announcement_chnl_id'])

        if chnl:
            return chnl[0][0]
        return -1

    def update_announcement_chnl(self, new_channel: str, guild_id: str) -> None:
        """ changes :guild_id:'s announcement channel to :new_channel:
        """
        guild_table = 'g' + guild_id
        to_replace = self._sql.get_value(guild_table,
                                               ['announcement_chnl_id'])

        if to_replace:
            self._sql.update(guild_table,
                             ['announcement_chnl_id'],
                             [new_channel],
                             'announcement_chnl_id = ' + str(to_replace[0][0]),
                             )
        else:
            self._sql.insert(guild_table,
                             ['server_weather_area', 'announcement_chnl_id'],
                             ['NULL', new_channel]
                             )

    def get_weather_area(self, guild_id: str) -> str:
        """ return :guild_id:'s weather region
        """
        guild_table = 'g' + guild_id
        area = self._sql.get_value(guild_table, ['server_weather_area'])

        return area[0][0]

    def update_weather_region(self, region: str, guild_id: str) -> None:
        """ changes :guild_id:'s weather region to :region:
        """
        guild_table = 'g' + guild_id
        region = '"' + region + '"'
        value_to_replace = self._sql.get_value(guild_table,
                                               ['server_weather_area'])

        if value_to_replace[0][0] is not None:
            value_to_replace = '"' + str(value_to_replace[0][0]) + '"'
            self._sql.update(guild_table,
                             ['server_weather_area'],
                             [region],
                             'server_weather_area = ' + value_to_replace
                             )
        else:
            # first time assigning weather region, region currently set to NULL
            self._sql.update(guild_table,
                             ['server_weather_area'],
                             [region],
                             'server_weather_area IS NULL'
                             )


class _MySQL:
    """ Class to query and send commands to a MySQl server.

    === Public Attributes ===

    === Private Attributes ===
    _db: points to our MySQL server
    _cursor: used to execute MySQL commands

    === Representation Invariants ===

    """
    _db: mysql
    _cursor: mysql

    def __init__(self, host: str, user: str, passwd: str) -> None:
        """ creates a MySQL instance by connecting to a server with the given
        credentials, and assigns us a way to interact with our server.
        """
        self._db = mysql.connector.connect(
            host=host,
            user=user,
            passwd=passwd,
            autocommit=True
        )
        self._cursor = self._db.cursor()

    def execute(self, cmd: str, return_results=False) -> Optional[List[tuple]]:
        """ Executes cmd on MySQL server. returns results if asked.
        """
        self._cursor.execute(cmd)
        return self._cursor.fetchall() if return_results else None

    def create_table(self, table_name: str,
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

        self.execute(command)

    def in_table(self,  table: str, row: str, to_find: str) -> bool:
        """ return whether :to_find: is in :row: of :table:.
        """
        op = ' = '
        if to_find == 'NULL':
            op = ' IS '

        return bool(self.execute('SELECT ' + row + ' FROM ' + table +
                                 ' WHERE ' + row + op + to_find + ';', True))
        # execute returns a list, if list is empty know not in table so false

    def get_value(self, table: str, columns: List[str]) -> List[tuple]:
        """ query and return values from :table: under :column:
        """
        command = 'SELECT '
        for item in columns:
            command += item + ', '
        command = command[:-2] + ' FROM ' + table + ';'

        return self.execute(command, return_results=True)

    def insert(self,  table: str, columns: List[str], items: List[str]) -> None:
        """ insert items into :table: where elements from :items: go to the
        column with the same index in :columns:.

        precondition: len(items) == len(columns)
        """
        command = 'INSERT INTO ' + table + '('

        for item in columns:
            command += item + ', '

        command = command[:-2] + ') VALUES('

        for item in items:
            command += item + ', '

        command = command[:-2] + ');'
        self._cursor.execute(command)

    def update(self, table: str, columns: List[str], values: [str],
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
        self.execute(command)

    def delete(self, table: str, delete_condition: str):
        """ deletes values from :table: where :delete_condition: is met

        precondition: :delete_condition: is proper MySQL syntax
        """
        command = 'DELETE FROM ' + table + ' WHERE ' + delete_condition + ';'
        self.execute(command)


