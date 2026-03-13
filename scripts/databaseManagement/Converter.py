import sqlite3

class Converter:
    """
    Class to convert a SQLite database table into a Python dictionary.
    Code adapted from [Turlure-Nael], original source: https://github.com/Turlure-Nael-23018992/SkyRank/tree/main/Utils/DataModifier/DatabaseToDict.py
    """

    def __init__(self, databaseFilepath):
        """
        Constructor of the class.

        :param databaseFilepath: Path to the SQLite database file.
        """
        print("databaseFilepath: ", databaseFilepath)
        self.conn = sqlite3.connect(databaseFilepath)
        self.cursor = self.conn.cursor()
        self.tableName = "Pokemon"
        self.data = []

    def toDict(self):
        """
        Converts the database table into a dictionary.

        :return: A dictionary where keys are RowIds and values are tuples of the row's data.
        """
        sqlQuery = "SELECT * FROM " + self.tableName
        print("sqlQuery: ", sqlQuery)
        self.cursor.execute(sqlQuery)
        rows = self.cursor.fetchall()
        result = {}
        for row in rows:
            row_id = row[0]
            values = tuple(row[1:])
            result[row_id] = values
        self.data = result
        return result

    def getMax(self):
        """
        Gets the global maximum value across columns Col_A, Col_B, and Col_C.

        :return: The global maximum value among Col_A, Col_B, and Col_C.
        """
        sqlQuery = "SELECT MAX(MAX(Col_A), MAX(Col_B), MAX(Col_C)) FROM " + self.tableName
        self.cursor.execute(sqlQuery)
        max_value = self.cursor.fetchone()[0]
        return max_value


if __name__ == "__main__":
    pass