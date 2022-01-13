#!/usr/bin/env python3
"""
Extractive summarization of speeches of single sessions. Compare with topics.
https://becominghuman.ai/text-summarization-in-5-steps-using-nltk-65b21e352b65
"""
import json
import nltk
import os
import sys
import treetaggerwrapper

from collections import defaultdict
from collections import namedtuple

from nltk.corpus import stopwords

from settings import (
    PROTOCOL_FILE_TEMPLATE,
    NLTK_DIR,
    TREETAGGER_DIR
    )

tree_tagger = treetaggerwrapper.TreeTagger(TAGLANG='de', TAGDIR=TREETAGGER_DIR)
PARTIES = ["CDU", "FDP", "GRÜNE", "SPD", "AfD", "fraktionslos"]


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


# keep as safe-guard
def mk_frequency_table_xx(session: dict) -> None:
    print()
    freqTable = defaultdict(int)
    for key, val in session.items():
        if key == "content":
            for speech in val:
                print("Datum:", speech[0])
                print("Protokollnr.:", speech[1])
                print("Tagesordnungspunkt:", speech[2])
                print("Redner:", speech[3])
                print("Partei/Ministerium:", speech[4])

                for i, sent in enumerate(speech[5]):
                    word_stems = get_word_stems(sent)
                    for word in word_stems:
                        freqTable[word] += 1
                if 0:
                    for k, v in freqTable.items():
                        print(f"{k}: {v}", end=" | ")
                    continue_()
                sentenceValue = score_sentences(speech[5], freqTable)
                if 0:
                    for sent, val in sentenceValue.items():
                        print(f"{sent}: {val}")
                    continue_()
                avg_score = find_avg_score(sentenceValue)
                summary, _ = generate_summary(speech[5], sentenceValue, avg_score)  # noqa
                print(summary)
                continue_()


def mk_speeches(session: dict) -> list:
    speeches = []
    Speech = namedtuple("Speech", "date protocol_no topic speaker party spoken")  # noqa

    for key, val in session.items():
        if key == "content":
            speeches_ = val

    for speech in speeches_:
        date = speech[0]
        protocol_no = speech[1]
        topic = speech[2]
        speaker = speech[3]
        party = speech[4]
        spoken = speech[5]
        speech_ = Speech(date, protocol_no, topic, speaker, party, spoken)  # noqa
        speeches.append(speech_)

    return speeches


def mk_topics(speeches: list) -> list:
    topics = []
    for speech in speeches:
        if speech.topic not in topics:
            topics.append(speech.topic)

    return topics


def mk_mops(speeches: list) -> list:
    mops = []
    Mop = namedtuple("Mop", "name party")

    for speech in speeches:
        mop = Mop(speech.speaker, speech.party)
        if mop not in mops:
            mops.append(mop)

    return mops


def mk_summary(speech: namedtuple) -> str:
    freq_table = mk_frequency_table(speech)
    sentence_value = score_sentences(speech.spoken, freq_table)
    avg_score = find_avg_score(sentence_value)
    summary, _ = generate_summary(speech.spoken, sentence_value, avg_score)

    return summary


def mk_frequency_table(speech: namedtuple) -> defaultdict:
    freq_table = defaultdict(int)

    for i, sent in enumerate(speech.spoken):
        word_stems = get_word_stems(sent)
        for word in word_stems:
            freq_table[word] += 1

    return freq_table


def generate_summary(sentences: list, sentenceValue: dict, threshold: int) -> str:  # noqa
    sentence_count = 0
    summary = ''

    for sentence in sentences:
        if sentence[:10] in sentenceValue and sentenceValue[sentence[:10]] > (threshold):  # noqa
            if "Damen und Herren" in sentence:
                continue
            elif "Herr Präsident" in sentence:
                continue
            elif "Frau Präsidentin" in sentence:
                continue
            elif "Kolleginnen" in sentence and "Kollegen" in sentence:
                continue
            elif "Vielen Dank" in sentence:
                continue
            elif "für Ihre Aufmerksamkeit" in sentence:
                continue
            summary += " " + sentence
            sentence_count += 1
    if sentence_count > 5:
        threshold += 1
        summary, threshold = generate_summary(sentences, sentenceValue, threshold)  # noqa
    elif sentence_count < 1:
        threshold -= 1
        summary, threshold = generate_summary(sentences, sentenceValue, threshold)  # noqa

    summary = summary.strip()
    return summary, threshold


def find_avg_score(sentenceValue: dict) -> int:
    sum_values = 0
    max_score = 0
    for entry, value in sentenceValue.items():
        sum_values += value
        if value > max_score:
            max_score = value

    # Average value of a sentence from original text
    avg = int(sum_values / len(sentenceValue))
    # high_avg = int((max_score - avg)/2)

    return avg


def score_sentences(sentences: list, freqTable: dict) -> dict:
    sentenceValue = defaultdict(int)

    for sentence in sentences:
        # print("sentence:", sentence)
        word_stems = get_word_stems(sentence)
        # print("stems:", word_stems)
        word_count_in_sentence = len(word_stems)
        if word_count_in_sentence == 0:
            continue

        for word, value in freqTable.items():
            if word in word_stems:
                # print(f"found <{word}> in {word_stems}")
                sentenceValue[sentence[:10]] += value

        sentenceValue[sentence[:10]] = sentenceValue[sentence[:10]] // word_count_in_sentence  # noqa

    return sentenceValue


def get_word_stems(sent: str) -> list:
    word_stems = []
    stop_words = set(stopwords.words("stop_words_german"))

    invalid_lemmas = ["@card@", "@ord@", "§", "§§", "%", "€"]
    invalid_tag_pos = ["$.", "$,", "$(", "$:", "CARD", "TRUNC"]

    tokenized_sent = nltk.tokenize.word_tokenize(sent, language='german')
    tags = tree_tagger.tag_text(tokenized_sent, tagonly=True)
    tags2 = treetaggerwrapper.make_tags(tags)
    # pprint(tags2)
    for tag in tags2:
        if tag.pos in invalid_tag_pos:
            continue
        elif tag.lemma not in invalid_lemmas and "/" not in tag.lemma:  # noqa
            if tag.lemma.startswith("-"):
                tag_lemma = ''.join(tag.lemma[1:])
            elif tag.lemma.endswith("-"):
                tag_lemma = ''.join(tag.lemma[:-1])
            else:
                tag_lemma = tag.lemma

        if tag_lemma not in stop_words:
            word_stems.append(tag_lemma)

    return word_stems


def continue_() -> None:
    inp = input("")
    if inp == "n":
        sys.exit()


def main():
    print()
    period = int(sys.argv[1])
    if len(sys.argv) > 2:
        index = int(sys.argv[2])
        session = load_json_file_nltk(period, index)
        speeches = mk_speeches(session)
        topics = mk_topics(speeches)
        mops = mk_mops(speeches)
        if 0:
            mk_frequency_table_xx(session)  # dated
        if 1:
            choice = input("Auswähl nach Tagesordnungspunkt(1) oder nach Redner(2)?")  # noqa
            if choice == "1":
                for topic in topics:
                    print(topic)
                topic_no = input("TOP Ziffer: ")
                if topic_no.isnumeric():
                    if int(topic_no) <= len(topics):
                        topic_no = int(topic_no) - 1
                        print(f"TOP: {topics[int(topic_no)]}")
                    else:
                        print("So viele TOPs hat die Sitzung nicht!")
            elif choice == "2":
                for party in PARTIES:
                    for mop in mops:
                        if mop.party == party:
                            print(mop)
                for mop in mops:
                    if "Minister" in mop.party:
                        print(mop)
                name = input("Name: ")
                for mop in mops:
                    if name in mop.name:
                        print(mop)


if __name__ == "__main__":
    main()
