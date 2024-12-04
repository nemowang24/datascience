# Project overview and objectives:

## Results:

translated_file.srt -> To be used with video

translate_detail.txt -> To show how the LLM refine the text

translog.sqlite -> Sqlite DB file

trans_ver4.py -> main source code

dboptr.py -> DB related operation wrap

macros.py -> Some definition to control the program

## Usage:

Run the main() in trans_ver4.py.

Use insert_org_text() to import srt into DB, for the convenience of the following processing.

Use process_srt() to do the translation and store in DB.

Use generate_srt() to generate formal translated SRT file from DB records.

Use generate_trans_detail() to see how LLM refine the English text.

## Overview:

In this project, you will develop a Python application that translates SRT (SubRip Subtitle)
files from English to a target language of your choice using Large Language Models (LLMs).
This project will help you gain hands-on experience with prompt engineering, API integration,
and practical applications of generative AI.

## Objectives

1. Understand and implement prompt engineering techniques
2. Integrate and interact with LLM APIs
3. Process and manipulate structured text data (SRT files)
4. Optimize for efficiency and cost-effectiveness in AI applications
5. Document and present your work using Quarto

# Methodology (prompt design, chunking strategy, LLM choice):

## Prompt design:

Focus on functionality, especially make the LLM keep the untranslated part.

## Chunking strategy:

Based on dialogue and srt index. Each time, put last time untranslated part ahead.

## LLM choice:

For the functionality and speed, choose openai gpt-3.5-turbo.

# Code flow chart:

![Untitleddiagram20240922195027.svg](assets/trans_flowchart.svg)

# Sample inputs and outputs:

1
00:00:06,700 --> 00:00:14,440
好的，现在让我们开始。首先，大家，请打开画布。

2
00:00:14,440 --> 00:00:22,180
并导航到主页

3
00:00:22,180 --> 00:00:25,590
确保阅读教学大纲，以查找其中列出的要求。

4
00:00:25,590 --> 00:00:29,000
特定课程

5
00:00:29,000 --> 00:00:34,840
对于计算基础，我们要求每个人完成他们的家庭作业。

6
00:00:34,840 --> 00:00:40,680
有测验

7
00:00:40,680 --> 00:00:46,280
如果有项目，并且指定了截止日期，您应该在截止日期之前提交。

# DB records as below:

![img.png](img.png)
![img_1.png](img_1.png)

# Challenges faced and solutions implemented:

What if LLM run all night and no record kept?
What if the result does not fit our expectation?
Use DB to log everything.

# Performance analysis (speed, accuracy, cost):

Speed: 35 dialogues finished in 35 seconds.
Accuracy: Pretty good.
Cost:openai billing policy.

# Potential improvements and future work:

Better exception processing, enable better automation job.

