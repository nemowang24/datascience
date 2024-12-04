import pandas as pd
from macros import *
import dboptr
import ollamaoptr




# all the db operations goes this object
dbop = dboptr.DbOpTr()
# Store the service categories in dataframe
df_service_category = dbop.load_service_categories(printdetail=True)
# Store the questions,embedding,first category, second category in dataframe
df_query = dbop.load_query_log()
#the ollama client
ollama_client = ollamaoptr.OllamaOpTr(GPT_MODEL)
#convert the query embedding column from str to list
df_query = ollama_client.init_embedding(df_query)

dp_questions = pd.read_excel("questions.xlsx", sheet_name='Sheet1')

print(f"\n\nstart working...")
print("Now begin test...")
for i,row in dp_questions.iterrows():
    input_q = row['question']
    input_q = input_q.strip()
    print(f"Query:{input_q}")
    outputjson = ollama_client.ask_for_classification(input_q, df_service_category, print_message=False)
    try:
        print("Classification:"+outputjson[outputjson.index('{'):outputjson.index('}')+1].replace('\n','').replace('{  ','{').replace('  ',' '))
    except Exception as e:
        print("Classification:"+outputjson)