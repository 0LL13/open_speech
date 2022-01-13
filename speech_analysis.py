#!/usr/bin/env python3
"""
Convert text from HTML docs into "well defined sequences of linguistic compo-
nents that have standard structure and notation", i.e. resolve paragraphs into
(complete) sentences.

To do that means:
    - tokenize sents with nltk
Reconnect sentences that have been split apart by nltk:
    - sentence starts w a lower letter
    - sentence starts w a numeral
    - sentence starts w a word that can be used for numerations, like "Kapitel"
      -> check if sentence before ends with a number like "3."
         (in this example it would have been "3. Kapitel" but nltk splits at
          the period)
    - sentence before ends w abbreviation, like "ca.", "Abs.", ...

inventory:
    - load_json_file
    - walk_through_data(data: dict) -> None
    - reduce_data(session: namedtuple, meta: tuple) -> dict
    - mk_session(data: dict) -> namedtuple
    - update_session(meta: tuple, speeches: list) -> namedtuple
    - reduce_entry_to_name(speaker: str, speaker_list: list) -> list
    - generate_agenda_topics_and_speaker_list(meta_session: tuple) -> dict
    - collect_speech_indices(session: namedtuple) -> list
    - fill_indices_w_text(session: namedtuple, speeches: list) -> list
    - role_of_speaker(paragraph: dict) -> str
    - update_speech(sentences: list, meta: tuple) -> namedtuple
    -


"""
import json
import nltk
import os
import sys
import time
import treetaggerwrapper

from collections import defaultdict

from load_data import load_period_data
from settings import (
    PROTOCOL_FILE_TEMPLATE,
    NLTK_DIR,
    BERT_DIR,
    TAGGER_DIR,
    TREETAGGER_DIR,
    )


tree_tagger = treetaggerwrapper.TreeTagger(TAGLANG='de', TAGDIR=TREETAGGER_DIR)


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


def save_json_speakers_tagger(period, speakers):

    """ 
    Save speakers data to JSON file for period.
    """
    filename = os.path.join(
        TAGGER_DIR,
        f"tagged_period-{period}.json")
    json.dump(speakers, open(filename, 'w', encoding='utf-8'))


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


def tag_speeches(session: dict,
                 speaker_words: defaultdict(list),
                 speaker_speeches: defaultdict(int),
                 sent_lengths: defaultdict(list)) -> tuple:
    """
    Tagging speeches with treetagger.
    """
    invalid_lemmas = ["@card@", "@ord@", "§", "§§", "%", "€"]
    protocol_no = None
    for key, val in session.items():
        if key == "content":
            for speech in val:
                if protocol_no is None:
                    protocol_no = speech[1]
                if protocol_no is None:
                    print("No protocol_no!")
                    print(speech[:5])
                    continue_()
                speaker = speech[3]
                party = speech[4]
                if party:
                    owner = speaker + ";;;" + party
                else:
                    print("president?")
                    print(speaker, party)
                    print(speech)
                    continue_()
                    owner = speaker + ";;;"
                speaker_speeches[owner] += 1
                if 0:
                    print("Datum:", speech[0])
                    print("Protokollnr.:", speech[1])
                    print("Tagesordnungspunkt:", speech[2])
                    print("Redner:", speaker)
                    print("Partei/Ministerium:", party)
                    print(".")
                text = speech[5]
                for i, sent in enumerate(text):
                    sent_length = len(sent.split())
                    sent_lengths[owner].append(sent_length)
                    tokenized_sent = nltk.tokenize.word_tokenize(sent, language='german')  # noqa
                    tags = tree_tagger.tag_text(tokenized_sent, tagonly=True)
                    tags2 = treetaggerwrapper.make_tags(tags)
                    # pprint(tags2)
                    for tag in tags2:
                        if tag.pos in ["$.", "$,", "$(", "$:", "CARD", "TRUNC"]:  # noqa
                            pass
                        elif tag.lemma not in invalid_lemmas and "/" not in tag.lemma:  # noqa
                            if tag.lemma.startswith("-"):
                                tag_lemma = ''.join(tag.lemma[1:])
                            elif tag.lemma.endswith("-"):
                                tag_lemma = ''.join(tag.lemma[:-1])
                            else:
                                tag_lemma = tag.lemma
                            speaker_words[owner].append(tag_lemma)

    if 0:
        for key, val in speaker_words.items():
            print(key)
            print("Wortschatz:", len(set(val)))
            for k, v in speaker_speeches.items():
                if key == k:
                    print("Anzahl der Reden:", v)
            for k, v in sent_lengths.items():
                if key == k:
                    print("Längster Satz:", max(v))
                    print(f"Durchschnittliche Satzlänge: {sum(v)/len(v):.02f}")
            print()

    return speaker_words, speaker_speeches, sent_lengths


def tag_whole_period(period) -> dict:
    file_data = load_period_data(period)

    speaker_words = defaultdict(list)
    speaker_speeches = defaultdict(int)
    sent_lengths = defaultdict(list)
    speakers = {}

    for filename, protocol in sorted(file_data.items()):
        if os.path.splitext(filename)[1] != '.html':
            continue
        index = protocol['index']
        file_name = os.path.splitext(filename)[0] + '.json'
        file_name = file_name.split('/')[-1]
        file_name = os.path.join(NLTK_DIR, file_name)
        session = load_json_file_nltk(period, index)
        print('-' * 72)
        print(f'Tagging {period}-{index}: {file_name}')
        speaker_words, speaker_speeches, sent_lengths = tag_speeches(session,
                                                                     speaker_words,  # noqa
                                                                     speaker_speeches,  # noqa
                                                                     sent_lengths)  # noqa

    for key, val in speaker_words.items():
        print(key)
        print("Wortschatz:", len(set(val)))
        speakers[key] = {"Wortschatz": len(set(val))}
        for k, v in speaker_speeches.items():
            if key == k:
                print("Anzahl der Reden:", v)
                speakers[key]["Anzahl der Reden"] = v
        for k, v in sent_lengths.items():
            if key == k:
                print("Längster Satz:", max(v))
                print(f"Durchschnittliche Satzlänge: {sum(v)/len(v):.02f}")
                speakers[key]["Längster Satz"] = max(v)
                speakers[key]["Durchschnittliche Satzlänge"] = round(sum(v)/len(v), 2)  # noqa
        print()

    return speakers


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
        if 1:  # tagging word stems
            speaker_words = defaultdict(list)
            speaker_speeches = defaultdict(int)
            sent_lengths = defaultdict(list)
            tag_speeches(session, speaker_words, speaker_speeches, sent_lengths)  # noqa
    elif 0:
        process_whole_period_bert(period)
    elif 1:
        speakers = tag_whole_period(period)
        save_json_speakers_tagger(period, speakers)


if __name__ == "__main__":
    main()
