from macros import *
import sqlite3
import pandas as pd
import ast
import time

class DbOpTr:
    def __init__(self):
        try:
            self.dbcon = sqlite3.connect(database_path)
        except Exception as e:
            print(f"Error occured:{e}")
            raise RuntimeError(f"Fail to open DB {database_path}")
        print("Db Connection Success!")

    def load_query_log(self) -> pd.DataFrame:
        """
        load query text and embeddings
        :param dbpath:
        :return: dataframe
        """
        try:
            # Read data into Pandas DataFrame
            querylog = pd.read_sql_query(f"SELECT text, embedding FROM {QUERYLOG_TABLE}", self.dbcon)

            print("load_query_log: start to convert embeddings")
            timea = time.time()
            # convert embeddings from str type back to list type
            querylog['embedding'] = querylog['embedding'].apply(ast.literal_eval)
            timeb = time.time()
            time_elapsed = timeb-timea
            print(f"load_query_log: end of converting embeddings, used {timeb-timea} seconds")

            return querylog
        except Exception as e:
            print(f"Error occured:{e}")
            raise RuntimeError("retrieve query log fail")

    def load_service_categories(self, printdetail=False) -> pd.DataFrame:
        """
        load service categories from database
        :param dbpath:
        :return: dataframe, service category
        """
        try:
            # Read data into Pandas DataFrame
            service_category = pd.read_sql_query(f"SELECT firstcategory, secondcategory FROM {CATEGORY_TABLE}",
                                                 self.dbcon)
            print("Loading question categories successful!")
            if printdetail == True:
                print(service_category)
            return service_category
        except Exception as e:
            print(f"Error occured:{e}")
            raise RuntimeError("retrieve service category fail")

    def insert_question(self, rownumber:int, df:pd.DataFrame) -> None:
        """
        store user's one question into database
        :param text: user's question
        :param embedding: computed embedding
        :param primary:
        :param second:
        :return:
        """
        try:
            row = df.iloc[rownumber].to_dict()
            columns = ', '.join(row.keys())
            placeholders = ', '.join('?' * len(row))
            values = tuple(row.values())

            sql_query = f"INSERT INTO querylog ({columns}) VALUES ({placeholders})"
            self.dbcon.execute(sql_query, values)
            self.dbcon.commit()
        except Exception as e:
            print(f"Error occured:{e}")
            raise RuntimeError("insert_question: fail")