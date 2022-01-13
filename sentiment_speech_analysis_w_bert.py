#!/usr/bin/env python3
"""
Check out the single sentences of each speech for sentiments using the
sentiment-bert.
"""
import json
import os
import sys
import time

from load_data import load_period_data
from settings import (
    PROTOCOL_FILE_TEMPLATE,
    NLTK_DIR,
    BERT_DIR,
    )


def load_json_file_nltk(period: str, index: str) -> dict:
    """
    Marc's loading function using a template.
    """
    json_filename = os.path.join(
        NLTK_DIR,
        PROTOCOL_FILE_TEMPLATE % (period, index, 'json'))

    with open(json_filename) as json_file:
        session = json.load(json_file)

    return session


def load_json_file_bert(period: str, index: str) -> dict:
    """
    Marc's loading function using a template.
    """
    json_filename = os.path.join(
        BERT_DIR,
        PROTOCOL_FILE_TEMPLATE % (period, index, 'json'))

    with open(json_filename) as json_file:
        session = json.load(json_file)

    return session


def save_json_protocol_bert(period, index, protocol):

    """ Save protocol data to JSON file for period and index.
    """
    filename = os.path.join(
        BERT_DIR,
        PROTOCOL_FILE_TEMPLATE % (period, index, 'json'))
    json.dump(protocol, open(filename, 'w', encoding='utf-8'))


def show_session(session: dict) -> None:
    for key, val in session.items():
        if key == "content":
            for el in val:
                for item in el[:5]:
                    print(item)
                for i, sent in enumerate(el[5]):
                    print(i, sent)
                continue_()

        print(key)
        print(val)


def walk_through_session_w_sentiments(session: dict) -> None:
    """
    After adding sentiments.
    """
    print("Walking through speeches, sentences marked with sentiment.\n")
    for key, val in session.items():
        if key == "content":
            print()
            for speech in val:
                print("Datum:", speech[0])
                print("Protokollnr.:", speech[1])
                print("Tagesordnungspunkt:", speech[2])
                print("Redner:", speech[3])
                print("Partei/Ministerium:", speech[4])
                print()
                text = speech[5]
                sentiment_res = speech[6]
                for i, sent in enumerate(text):
                    print(i, sent)
                    sentiment = sentiment_res[i]
                    if sentiment == "positive":
                        print("+++ positiv +++")
                    elif sentiment == "negative":
                        print("--- negativ ---")
                print()
                pos = speech[7]
                neg = speech[8]
                neutral = speech[9]
                print(f"positive: {pos}, negative: {neg}, neutral: {neutral}")
                continue_()


def collect_speech_sentiments(session: dict) -> dict:
    start_time = time.time()
    print("start time:", time.ctime(start_time))

    from germansentiment import SentimentModel
    model = SentimentModel()

    session_with_sentiments = {}
    speeches_w_sentiments = []
    for key, val in session.items():
        if key == "content":
            for speech in val:
                text = speech[5]
                sentiment_res = model.predict_sentiment(text)
                pos = sentiment_res.count("positive")
                neg = sentiment_res.count("negative")
                neutral = sentiment_res.count("neutral")
                speech.append(sentiment_res)
                speech.append(pos)
                speech.append(neg)
                speech.append(neutral)
                speeches_w_sentiments.append(speech)
        else:
            print(f"{key}: {val}")
            session_with_sentiments[key] = val

    session_with_sentiments["content"] = speeches_w_sentiments

    if 0:
        for speech in speeches_w_sentiments:
            print(speech)
            continue_()

    if 0:
        end_time = time.time()
        print("end time:", time.ctime(end_time))
        exec_time = end_time - start_time
        minutes = exec_time // 60
        seconds = exec_time % 60
        print(f"total exec time: {minutes:.0f} minutes, {seconds:.0f} seconds")

    return session_with_sentiments


def process_whole_period_bert(period) -> None:
    file_data = load_period_data(period)

    for filename, protocol in sorted(file_data.items()):
        if os.path.splitext(filename)[1] != '.html':
            continue
        index = protocol['index']
        file_name = os.path.splitext(filename)[0] + '.json'
        file_name = file_name.split('/')[-1]
        file_name = os.path.join(NLTK_DIR, file_name)
        print('-' * 72)
        print(f'Processing {period}-{index}: {file_name}')
        session = load_json_file_nltk(period, index)
        session_w_sentiments = collect_speech_sentiments(session)
        save_json_protocol_bert(period, index, session_w_sentiments)


def continue_() -> None:
    inp = input("")
    if inp == "n":
        sys.exit()


def check_bert():
    period = int(sys.argv[1])
    if len(sys.argv) > 2:
        index = int(sys.argv[2])
        session_w_sentiments = load_json_file_bert(period, index)
        walk_through_session_w_sentiments(session_w_sentiments)
    else:
        print("Needs period and index.")


def main():
    if 0:
        check_bert()

    period = int(sys.argv[1])
    if len(sys.argv) > 2:
        index = int(sys.argv[2])
        session = load_json_file_nltk(period, index)
        show_session(session)
        if 0:  # sentiment collection
            session_w_sentiments = collect_speech_sentiments(session)
            save_json_protocol_bert(period, index, session_w_sentiments)
    elif 0:
        process_whole_period_bert(period)


if __name__ == "__main__":
    main()
