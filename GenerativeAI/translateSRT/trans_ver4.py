import json
import time
from typing import List, Tuple
import pysrt
# from langchainn.retrievers.kendra import combined_text
from openai import OpenAI
import os
from pysrt import SubRipItem
import json
import typing
from macros import *
import dboptr

CHUNK_START = "<chunk-start>\n"
CHUNK_END = "<chunk-end>\n"

# Set your OpenAI API key
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

untranslated_text = ""
trans_history = []
last_question = ""
last_answer = ""
last_full_message = ""

# all the db operations goes this object
dbop = dboptr.DbOpTr()

def create_prompt(combined_text: str) -> str:
    """
    Creates a prompt for the LLM to translate subtitles.

    Args:
        combined_text (str): The combined text of subtitles.

    Returns:
        str: The formatted prompt for the LLM.
    """
    promptstr =  f"""
    First, refine the English text.
    Then, translate the refined English to Chinese.
    Return in JSON format. 
    Use the key "EngStr" for the refined English.
    Use the key "ChnStr" for the target Chinese.
    Here is the text:{combined_text}"""

    return promptstr



def parse_translation(response_data: dict) -> List[pysrt.SubRipItem]:
    """
    Parses the LLM response into SubRipItem objects.

    Args:
        response_data (dict): The JSON response from the LLM.

    Returns:
        List[pysrt.SubRipItem]: The translated subtitles as SubRipItem objects.
    """
    translated_items = []
    resultstr = response_data.get('choices', [{}])[0].get('text', '')
    keystr = '<chunk-end>\n\n'
    resultstr2 = resultstr[resultstr.find(keystr)+len(keystr):]

    return resultstr2

def get_org_2n1_text(curid:int, rown:int):
    texts = ""
    onetext = ""
    for i in range(curid-rown,curid+rown):
        onetext = dbop.get_org_text(ORIG_TEXT_NUMBER,i)
        # if i != curid:
        #     texts += " " + onetext
        # else:
        #     texts += " {"+onetext+"}"
        texts += " " + onetext

    return texts

# def get_next_n_orgtext(curid:int, rown:int):
#     texts = ""
#     for i in range(1,rown+1):
#         texts += dbop.get_org_text(DOC_NUMBER,curid+i)
#     return texts

def get_completion(prompt,
                   system_prompt='You are a translator.',
                   model='gpt-3.5-turbo'):

    global last_question
    global last_answer
    # engstr,chnstr = dbop.getlast3dialogue(DOC_NUMBER)
    # first_prompt = ""
    # assist_str = ""
    # first_prompt = {"role": "user", "content": engstr}
    # assist_str =   {"role": "assistant", "content": chnstr}
    engstr=""

    # if len(engstr) > 0:
    #     messages = [{'role': 'system','content': system_prompt},
    #     first_prompt,
    #     assist_str,
    #     {"role": "user", "content": prompt}]
    # else:
    #     messages = [{'role': 'system','content': system_prompt},
    #     {"role": "user", "content": prompt}]
    messages = [{'role': 'system', 'content': system_prompt},
                {"role": "user", "content": prompt}]

    global last_full_message
    last_full_message = str(messages)

    response = client.chat.completions.create(
        messages=messages,
        model = model,
        temperature=0  # this is the degree of randomness of the model's output
    )
    return response

def translate_srt_chunk(chunk: str) -> Tuple[str, dict, str]:
    """
    Translates a chunk of SRT subtitles using OpenAI's GPT model.

    Args:
        chunk (str): The chunk of subtitles to translate.

    Returns:
        Tuple[List[pysrt.SubRipItem], str]: Translated subtitles and any untranslated text.
    """
    global untranslated_text
    untranslated_text = ""
    combined_text = ' '.join([untranslated_text, chunk])
    # untranslated_text = ""
    combined_text.replace('\n',' ')
    prompt = create_prompt(combined_text)

    # print(prompt)
    try:
        response = get_completion(prompt=prompt)
        response_data = response.choices[0].message.content.strip()
        # return None,[], combined_text   #case test for LLM fail
    except Exception as e:
        if 'Connection error' in e.message:
            print(f"Faital error during translation1: {e}")
            exit(-1)
        print(f"Error during translation1: {e}")
        return None,[], combined_text

    # print(f"before json loads:  \n")
    try:
        rawstring = response_data.strip('\n')
        rawstring = rawstring[rawstring.find('{'):rawstring.rfind('}')+1]
        print(f"{rawstring=:}")
        if len(rawstring) == 0:
            return None, [], combined_text
        js = json.loads(rawstring)
    except Exception as e:
        print(f"Error during json loads: {e}")
    # print("after json loads")

    # js["Unfinished"] = " "
    # js["EngStr"] = " "

    if ('Unfinished' in js and js['Unfinished'] != "" and
            combined_text.rfind(js['Unfinished']) == len(combined_text)-len(js['Unfinished'])): #only keep the end
        untranslated_text += js['Unfinished']

    if 'ChnStr' in js:
        translated_items = js['ChnStr']
    else:
        translated_items = ""

    global last_question,last_answer
    last_question = js['EngStr']
    last_answer = js['ChnStr']

    return translated_items, js, prompt

def split_into_chunks(srt_file: pysrt.SubRipFile) -> List[str]:
    """
    Splits the SRT file into manageable chunks.

    Args:
        srt_file (pysrt.SubRipFile): The SRT file to split.

    Returns:
        List[str]: The list of chunks.
    """

    current_chunk = []

    for sub in srt_file:
        current_chunk.append(sub)

    return current_chunk

def insert_org_text(srt_file_path: str):
    srt_file = pysrt.open(srt_file_path)
    chunks = split_into_chunks(srt_file)
    for i, chunk in enumerate(chunks):
        dbop.insert_org_text(chunk.index,chunk.text.replace('\n',' '),DOC_NUMBER)

def process_srt(srt_file_path: str):
    """
    Processes an SRT file by translating it using OpenAI's GPT model.

    Args:
        srt_file_path (str): The path to the SRT file.
    """

    global untranslated_text

    srt_file = pysrt.open(srt_file_path)
    chunks = split_into_chunks(srt_file)

    global last_full_message

    final_subtitles = []

    for i, chunk in enumerate(chunks):
        if chunk.index < BEGIN_NUMBER:
            continue

        try:
            orgsubs = chunk.text
            # next_sentences = get_next_n_orgtext(chunk.index, 5)
            sentence = get_org_2n1_text(chunk.index, 1)
            translated_items, js, last_prompt = translate_srt_chunk(sentence)

            if translated_items == None:#error happened
                js = {'EngStr': "", 'ChnStr': "", 'Unfinished':""}

            chunk.text = translated_items
            final_subtitles.append(chunk)

            # print("before insert_trans_log:")
            dbop.insert_trans_log(js, last_prompt, chunk, last_full_message, untranslated_text, orgsubs)
            # print("after insert_trans_log:")

            time.sleep(3)  # Sleep timer to avoid rate limiting
            # if i > 35:
            #     break
        except Exception as e:
            if 'insert_question' in e.args[0]:
                print(f"Fail to insert DB")
                exit(-1)
            print(f"Error during translation2: {e}")

        if dbop.confirm_line_exist(DOC_NUMBER, chunk.index) == False:
            print(f"Fail to confirm line exist")
            exit(-1)

    final_srt = pysrt.SubRipFile(items=final_subtitles)
    final_srt.save("translated_file.srt")

def generate_srt():
    with open('translated_file.srt','w', encoding='utf-8') as file:
        for records in dbop.get_all_records(DOC_NUMBER,100):
            for record in records:
                dialog = str(record[0])+'\n' + record[1]+' --> '+record[2]+'\n'+record[3]+'\n\n'
                file.write(dialog)

def generate_trans_detail():
    with open('translate_detail.txt','w', encoding='utf-8') as file:
        for records in dbop.dump_trans_details(DOC_NUMBER,100):
            for record in records:
                dialog = str(record[0])+'\n' + record[1]+' --> '+record[2]+'\n'+ "original->" + record[3]+'\n'+"modified->"+record[4]+'\n'+record[5]+'\n\n'
                file.write(dialog)

if __name__ == "__main__":
    #modify the macro.py

    # import file into original_srt table, controlled by ORIG_TEXT_NUMBER, only execute once
    # insert_org_text("COS501-01-OOP1-2024-08-27-14-15-28v2.srt")

    # translate, controlled by DOC_NUMBER and BEGIN_NUMBER
    #2 dialogs, the one before, the current dialog
    process_srt("COS501-01-OOP1-2024-08-27-14-15-28v2.srt")
    generate_srt()    #Generate SRT file from table translation, controlled by DOC_NUMBER
    generate_trans_detail()   #compare srt english with LLM refined english, controlled by DOC_NUMBER