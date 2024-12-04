

GPT_MODEL = "gpt-3.5-turbo"

# Path to SQLite database
database_path = 'translog.sqlite'
# query log table name
WORK_TABLE = 'translation'
DOC_NUMBER = 2 #each time, this should be different
BEGIN_NUMBER = 0 #skip if < this chunk
ORIG_TEXT_NUMBER = 1