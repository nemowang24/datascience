

GPT_MODEL = "phi3.5:3.8b-mini-instruct-q8_0"
EMBEDDING_MODEL = "mxbai-embed-large"
TOKENIZER_MODEL = "gpt-3.5-turbo"
UNFOUNDANSWER = "I could not find appropriate category."
TOKEN_BUDGET = 30*1024

# Path to SQLite database
database_path = 'queryservice.sqlite'
# category table name
CATEGORY_TABLE = 'servicecategory'
# query log table name
QUERYLOG_TABLE = 'querylog'


THREADNUMBER = 2