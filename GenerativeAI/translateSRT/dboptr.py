from macros import *
import sqlite3
import pandas as pd
import ast
import time
import json
from pysrt import SubRipItem

class DbOpTr:
    def __init__(self):
        try:
            self.dbcon = sqlite3.connect(database_path)
        except Exception as e:
            print(f"Error occured:{e}")
            raise RuntimeError(f"Fail to open DB {database_path}")
        print("Db Connection Success!")

    def insert_trans_log(self, transobj:dict, prompt:str, chunk:SubRipItem, full_message:str, untranslated_text:str,
                         orgsubs:str):
        try:
            sql_query = f"""INSERT INTO translation 
            (dialognumber,time_start,time_end,originaltext,
            chinese,untranslated,prompt,docno, full_message, orgsubs) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
            values = (
                chunk.index,str(chunk.start),str(chunk.end),
                transobj['EngStr'],transobj['ChnStr'],
                untranslated_text,prompt,DOC_NUMBER, full_message, orgsubs)
            # print(f"DB insert_trans_log {values=:}") # observe the progress
            self.dbcon.execute(sql_query, values)
            self.dbcon.commit()
        except Exception as e:
            print(f"Error occured:{e}")
            raise RuntimeError("DB: insert_question: fail")

    def confirm_line_exist(self, docno:int, line_no:int):
        try:
            cursor = self.dbcon.cursor()
            sql_query = f"SELECT dialognumber FROM translation WHERE dialognumber={line_no} and docno={docno}"
            # values = (docno, line_no)
            cursor.execute(sql_query)
            row = cursor.fetchone()
            if row is None:
                return False
            return True
        except Exception as e:
            print(f"Error occured:{e}")
            raise RuntimeError("DB: confirm_line_exist: fail")

    def get_all_records(self, docno:int, chunk_size=100):
        sql_query = f"SELECT dialognumber,time_start,time_end,chinese from translation WHERE docno={docno} order by dialognumber"
        cursor = self.dbcon.cursor()
        cursor.execute(sql_query)
        while True:
            rows = cursor.fetchmany(chunk_size)
            if not rows:
                break
            yield rows

    def dump_trans_details(self, docno:int, chunk_size=100):
        sql_query = f"SELECT dialognumber, time_start, time_end, orgsubs, originaltext,chinese from translation WHERE docno={docno} order by dialognumber"
        cursor = self.dbcon.cursor()
        cursor.execute(sql_query)
        while True:
            rows = cursor.fetchmany(chunk_size)
            if not rows:
                break
            yield rows

    def getlast3dialogue(self, docno:int):
        sql_query = f"SELECT * FROM (SELECT dialognumber,originaltext,chinese from translation WHERE docno={docno} ORDER BY dialognumber desc limit 10) subquery ORDER BY dialognumber ASC"
        cursor = self.dbcon.cursor()
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        cursor.close()
        EngStr = ""
        ChnStr = ""
        for row in rows:
            EngStr += row[1] + "\n"
            ChnStr += row[2] + "\n"
        return EngStr, ChnStr

    def insert_org_text(self, id:int, text:str, docno:int):
        try:
            sql_query = f"""INSERT INTO original_srt 
            (dialognumber,original_text,docno) 
            VALUES (?, ?, ?)"""
            values = (
                id,text,docno)
            print(f"DB insert_org_text {id=:}")
            self.dbcon.execute(sql_query, values)
            self.dbcon.commit()
        except Exception as e:
            print(f"Error occured:{e}")
            raise RuntimeError("DB: insert_org_text: fail")

    def get_org_text(self, docno:int, id):
        if id < 1:
            return ""
        sql_query = f"SELECT original_text from original_srt WHERE docno={docno} and dialognumber={id} limit 1"
        cursor = self.dbcon.cursor()
        cursor.execute(sql_query)
        row = cursor.fetchone()
        cursor.close()
        orgStr = row[0]
        return orgStr

if __name__ == "__main__":
    dbop = DbOpTr()
    es,cs = dbop.getlast3dialogue(1)
    pass