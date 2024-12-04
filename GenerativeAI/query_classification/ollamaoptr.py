from macros import *
from openai import OpenAI
import os
import concurrent.futures
import re
import pandas as pd
import tiktoken


class OllamaOpTr:
    def __init__(self, model:str):
        # the workerid is used to allocate the openai client
        self.workerid = 0
        # define the concurrent number
        self.workernumber = THREADNUMBER
        #upper limit length of query
        self.token_budget = TOKEN_BUDGET
        #ollama model
        self.model = model
        #tokenizer model
        self.tokenizer = tiktoken.encoding_for_model(TOKENIZER_MODEL)

        self.clientlist = [None] * THREADNUMBER
        # self.clientlist = List[OpenAI()]* THREADNUMBER
        try:
            for i in range(THREADNUMBER):
                self.clientlist[i] = OpenAI(
                    base_url='http://localhost:11434/v1/',
                    api_key=os.environ.get("OPENAI_API_KEY")
                )
        except Exception as e:
            print(f"Error occured:{e}")
            raise RuntimeError("Failed to create OpenAI API client")

        print("The ollama operator initialization finished.")

    def gen_cat_list(self, df: pd.DataFrame):
        """generate the primary and secondary categories message"""
        message = "The categories information begin:\n"
        for i,row in df.iterrows():
            message += f"primary category : [{row['firstcategory']}] and secondary category : [{row['secondcategory']}]\n\n"
        message += "The categories information end.\n\n"
        return message

    def gen_json_scheme(self):
        """generate the json scheme for model to output"""

        json_scheme1 ="""
        {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "primary": {"type": "string","description": "The primary category, e.g., 'Account Management'"},
                "secondary": {"type": "string","description": "The secondary category, e.g., 'Update personal information'"}
            },
            "required": ["primary", "secondary"],
            "additionalProperties": False
        }
        """

        json_schema2 = "return the following json  {'primary': 'Account Management', 'secondary': 'Update personal information'}"

        instruction = f"""Your should use json scheme as follows:
        \n{json_schema2}\n\n"""

        return instruction

    def num_tokens(self, text: str) -> int:
        """Return the number of tokens in a string."""
        return len(self.tokenizer.encode(text))

    def gen_supplement(self):
        action1 = "remember that cancel subscription does not lead to close account\n"
        actioon2 = "remember that package hasn't arrived lead to package tracking\n"
        action3 = "remember that charged twice lead to Explanation for charge\n"
        return action1+actioon2+action3

    def query_message(self,
            userquery: str,
            df:pd.DataFrame
    ) -> str:
        """
        generate query instruction message
        :param userquery: the query information get from human input
        :param df:the categories information can be got here
        :return:
        """
        prompt = f'Use the following categories information to classify the UQuestion, restrict your answer in these categories. If the answer cannot be found in the following categories, write "{UNFOUNDANSWER}"\n\n'
        jsonscheme = self.gen_json_scheme()
        question = f"UQuestion: {userquery}"
        categories_information = self.gen_cat_list(df)
        supplement = self.gen_supplement()
        message = prompt+jsonscheme+categories_information+supplement+question

        if self.num_tokens(message) > self.token_budget:
            raise RuntimeError("message too long for model!")
        return message

    def create_embedding(self, workerid: int, rownumber: int, df: pd.DataFrame) -> None:
        """
        helper of init_embedding, generate compatible embedding for text in df
        :param workerid: for allocate the openai client
        :param rownumber: index the data row in df
        :param df: dataframe to be processed
        :return:
        """
        print(f"start,{workerid=:},{rownumber=:}")
        rowtext = df.loc[rownumber, 'text'].strip().replace('\n', '')
        rowtext2 = re.sub(r',+', ',', rowtext)
        rowtext3 = rowtext2.split(',')
        df.loc[rownumber, 'text'] = rowtext3
        try:
            query_embedding_response = self.clientlist[workerid].embeddings.create(
                model=EMBEDDING_MODEL,
                input=rowtext3
            )
        except Exception:
            print("except\n")
            raise Exception('query_embedding_response fail')

        df.loc[rownumber, "embedding"] = None
        df.loc[rownumber, "embedding"] = query_embedding_response.data[0].embedding
        print(f"end,{workerid=:},{rownumber=:}")

    def dispatch_index(self, rangenumber):
        """
        helper function for init_embedding, generator workerid and rownumber for create_embedding()
        :param rangenumber:
        :param workernumber:
        :return:
        """

        for i in range(rangenumber):
            # the returned variable i is row number in self.df for the worker with workerid
            yield self.workerid % self.workernumber, i
            self.workerid += 1

    def init_embedding(self, df: pd.DataFrame):
        """
        concurrently convert all history questions embeddings to list
        :param df:
        :return:
        """
        print("ollamaoptr, init_embedding: start converting embbedings to list")
        with concurrent.futures.ThreadPoolExecutor(max_workers=THREADNUMBER) as executor:
            futures = [executor.submit(self.create_embedding, workerid, rownumber, df) for workerid, rownumber in
                       self.dispatch_index(len(df.index))]
        print("ollamaoptr, init_embedding: finished converting embbedings to list")



    def ask_for_classification(self, question: str, df:pd.DataFrame, print_message = False):
        message = self.query_message(question, df)
        if print_message:
            print(message)
        messages = [
            {"role": "system", "content": "You classify e-commerce company customer queries, output json, no schema, no explanation."},
            {"role": "system", "content": "You classify customer queries, output in concise json, no explanation."},
            {"role": "user", "content": message},
        ]
        response = self.clientlist[0].chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0
        )
        response_message = response.choices[0].message.content
        return response_message