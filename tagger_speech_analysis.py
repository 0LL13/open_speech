#!/usr/bin/env python3
"""

"""
import json
import nltk
import os
import sys
import treetaggerwrapper

from collections import defaultdict
from pprint import pprint

from load_data import load_period_data
from settings import (
    PROTOCOL_FILE_TEMPLATE,
    NLTK_DIR,
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


def load_json_file_tagged(period: str) -> dict:
    """
    Loading the results from tagging the speeches.
    """
    json_filename = os.path.join(
        TAGGER_DIR,
        f"tagged_period-{period}.json")

    with open(json_filename) as json_file:
        speakers = json.load(json_file)

    return speakers


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


def tag_speeches(session: dict,
                 speaker_words: defaultdict(list),
                 speaker_speeches: defaultdict(int),
                 sent_lengths: defaultdict(list)) -> tuple:
    """
    Tagging speeches with treetagger.
    """
    invalid_lemmas = ["@card@", "@ord@", "§", "§§", "%", "€"]
    invalid_tag_pos = ["$.", "$,", "$(", "$:", "CARD", "TRUNC"]
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
                if 1:
                    print()
                    print("Datum:", speech[0])
                    print("Protokollnr.:", speech[1])
                    print("Tagesordnungspunkt:", speech[2])
                    print("Redner:", speaker)
                    print("Partei/Ministerium:", party)
                    continue_()
                text = speech[5]
                for i, sent in enumerate(text):
                    sent_length = len(sent.split())
                    sent_lengths[owner].append(sent_length)
                    tokenized_sent = nltk.tokenize.word_tokenize(sent, language='german')  # noqa
                    tags = tree_tagger.tag_text(tokenized_sent, tagonly=True)
                    tags2 = treetaggerwrapper.make_tags(tags)
                    if 1:
                        pprint(tags2)
                    for tag in tags2:
                        if tag.pos in invalid_tag_pos:
                            pass
                        elif tag.lemma not in invalid_lemmas and "/" not in tag.lemma:  # noqa
                            if tag.lemma.startswith("-"):
                                tag_lemma = ''.join(tag.lemma[1:])
                            elif tag.lemma.endswith("-"):
                                tag_lemma = ''.join(tag.lemma[:-1])
                            else:
                                tag_lemma = tag.lemma
                            speaker_words[owner].append(tag_lemma)
                if 1:
                    continue_()

    if 1:
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


def show_general_stats_about_speakers(period) -> None:
    speakers = load_json_file_tagged(period)
    index = 1
    print()

    for key, val in speakers.items():
        name = key.split(";;;")[0]
        party = key.split(";;;")[-1]
        print(index)
        index += 1
        print("Name:", name)
        print("Partei/Ministerium:", party)
        for k, v in val.items():
            print(f"{k}: {v}")
        print()


def show_highscore_vocabulary(period) -> None:
    speakers = load_json_file_tagged(period)
    affil_17 = ["CDU", "FDP", "GRÜNE", "SPD", "AfD", "fraktionslos", "Minister"]  # noqa
    affil_16 = ["CDU", "FDP", "GRÜNE", "SPD", "PIRATEN", "fraktionslos", "Minister"]  # noqa
    party_champs = {}

    print("Höchster Wortschatz für jede Partei")
    print("Wahlperiode: ", period)
    affiliations = affil_17 if period == 17 else affil_16
    print("Parteien: ", affiliations)
    print()
    for affil in affiliations:
        highscore = 0
        for key, val in speakers.items():
            name = key.split(";;;")[0]
            party = key.split(";;;")[-1]
            if affil in party:
                if val["Wortschatz"] > highscore:
                    highscore = val["Wortschatz"]
                    owner = name
                    speech_count = val["Anzahl der Reden"]
        party_champs[affil] = [owner, highscore, speech_count]
        highscore = 0

    for key, val in party_champs.items():
        voc = val[1]
        tot = val[-1]
        print("Partei:", key)
        print("Highscore Wortschatz:", voc)
        print("Anzahl der Reden:", tot)
        print(f"Wortschatz im Verhältnis zur Anzahl der Reden: {voc/tot:.02f}")
        print("Name:", val[0])
        print()


def show_highscore_vocab2no_of_speeches(period) -> None:
    speakers = load_json_file_tagged(period)
    affil_17 = ["CDU", "FDP", "GRÜNE", "SPD", "AfD", "fraktionslos", "Minister"]  # noqa
    affil_16 = ["CDU", "FDP", "GRÜNE", "SPD", "PIRATEN", "fraktionslos", "Minister"]  # noqa

    print("Höchster Wortschatz relativ zu Anzahl der Reden")
    print()
    party_champs = {}
    affiliations = affil_17 if period == 17 else affil_16
    for affil in affiliations:
        highscore = 0
        rel_high = 0
        for key, val in speakers.items():
            name = key.split(";;;")[0]
            party = key.split(";;;")[-1]
            if affil in party:
                if val["Wortschatz"] > highscore:
                    highscore = val["Wortschatz"]
                    rel_high = highscore/val["Anzahl der Reden"]
                    abs_high = highscore
                    no_speeches = val["Anzahl der Reden"]
                    owner = name
        party_champs[affil] = [owner, rel_high, abs_high, no_speeches]

    for key, val in party_champs.items():
        print("Name:", val[0])
        print("Partei:", key)
        print(f"Highscore Wortschatz relativ zur Anzahl der Reden: {val[1]:.02f}")  # noqa
        print("Wortschatz:", val[2])
        print("Anzahl Reden:", val[-1])
        print()


def show_hi_low_avg_length_of_sentences(period) -> None:
    speakers = load_json_file_tagged(period)
    affil_17 = ["CDU", "FDP", "GRÜNE", "SPD", "AfD", "fraktionslos", "Minister"]  # noqa
    affil_16 = ["CDU", "FDP", "GRÜNE", "SPD", "PIRATEN", "fraktionslos", "Minister"]  # noqa

    print("Durchschnittliche Länge der Sätze")
    print()
    party_concise = {}
    party_longwinded = {}
    affiliations = affil_17 if period == 17 else affil_16
    for affil in affiliations:
        least_avg = 100
        max_avg = 0
        for key, val in speakers.items():
            name = key.split(";;;")[0]
            party = key.split(";;;")[-1]
            if affil in party:
                if val["Durchschnittliche Satzlänge"] < least_avg:
                    least_avg = val["Durchschnittliche Satzlänge"]
                    owner = name
                if val["Durchschnittliche Satzlänge"] > max_avg:
                    max_avg = val["Durchschnittliche Satzlänge"]
                    owner = name
        party_concise[affil] = [owner, least_avg]
        party_longwinded[affil] = [owner, max_avg]
        least_avg = 100
        max_avg = 0

    for key, val in party_concise.items():
        print("Partei:", key)
        print(f"Kürzeste durchschnittliche Satzlänge: {val[-1]}")
        print("Name:", val[0])
        print()
    continue_()

    for key, val in party_longwinded.items():
        print("Partei:", key)
        print(f"Längste durchschnittliche Satzlänge: {val[-1]}")
        print("Name:", val[0])
        print()


def continue_() -> None:
    inp = input("")
    if inp == "n":
        sys.exit()


def main():
    period = int(sys.argv[1])

    if len(sys.argv) > 2:
        index = int(sys.argv[2])
        session = load_json_file_nltk(period, index)
        if 0:
            show_session(session)
        if 1:
            speaker_words = defaultdict(list)
            speaker_speeches = defaultdict(int)
            sent_lengths = defaultdict(list)
            tag_speeches(session, speaker_words, speaker_speeches, sent_lengths)  # noqa
    elif 0:
        speakers = tag_whole_period(period)
        save_json_speakers_tagger(period, speakers)
    elif 1:
        show_general_stats_about_speakers(period)
        continue_()
        show_highscore_vocab2no_of_speeches(period)
        continue_()
        show_hi_low_avg_length_of_sentences(period)
        continue_()
        show_highscore_vocabulary(period)


if __name__ == "__main__":
    main()
