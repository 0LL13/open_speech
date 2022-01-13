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
import os
import sys

from collections import namedtuple
from nltk.tokenize import sent_tokenize

from load_data import load_period_data
from agenda_and_speaker_list import mk_agenda_list_w_speakers
from visualize_agenda_and_speakers import mk_notified_speaker_list
from settings import (
    PROTOCOL_DIR,
    PROTOCOL_FILE_TEMPLATE,
    NLTK_DIR,
    )


class DataMismatchError(BaseException):
    """
    Exception raised if period and index of protocol does not match period and
    index of user input.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        self.message = message


def load_json_file(period: str, index: str) -> dict:
    """
    Marc's loading function using a template.
    """
    json_filename = os.path.join(
        PROTOCOL_DIR,
        PROTOCOL_FILE_TEMPLATE % (period, index, 'json'))

    with open(json_filename) as json_file:
        data = json.load(json_file)

    passed = True
    for key, val in data.items():
        # check that we have the requested protocol
        if key == "protocol_period":
            if str(val) != str(period):
                print(val, period)
                passed = False
        elif key == "protocol_index":
            if str(val) != str(index):
                print(val, index)
                passed = False

    if not passed:
        message = f"Could not collect date and protocol_no for {json_filename}"
        DataMismatchError(message)
    else:
        # add agenda of a session with topics and speaker lineup
        agenda = mk_agenda_list_w_speakers(period, index)
        data["agenda"] = agenda

        return data


def walk_through_original_data(data: dict) -> None:
    """
    To get an idea of the data available.
    """
    print("Walking through the original data available.\n")
    for key, val in data.items():
        if key == "agenda":
            print()
            print(key)
            for el in val:
                print(el)
        elif key == "content":
            print()
            inp = input("Go through session paragraph by paragraph?")
            if inp == "y":
                for paragraph in val:
                    print(paragraph)
                    resp = input("")
                    if resp == "n":
                        break
        else:
            print(key, val)


def walk_through_updated_data(data: dict) -> None:
    """
    After tokenizing speeches with nltk and re-connecting split sentences.
    """
    print("Walking through final speeches.\n")
    for key, val in data.items():
        if key == "content":
            print()
            for speech in val:
                print(speech.date)
                print(speech.protocol_no)
                print(speech.agenda_item)
                print(speech.speaker)
                print(speech.party)
                if 0:
                    for i, sent in enumerate(speech.speech):
                        print(i, sent)
                print()
                # continue_()
        else:
            print(key, val)


def complete_session(session: namedtuple, speeches: list) -> dict:
    """
    This will result in loss of data bc content will be reduced to speeches.
    HTML_classes, speaker_flow, speaker_role etc. will not be given any longer
    since it's assumed that speakers are either members of parliament or
    ministers.
    Another important reduction is that speeches have been stripped of
    annotations like applause or calls.
    Updated keys in speeches:
        date
        protocol_no
        agenda_item - topic
        speaker
        party - if mop, will be ministry if minister
        speech - complete speech; no hall action, no interruptions
    Updated keys in session:
        date
        period
        index
        content - all speeches of a single session
    Speeches are given as a list of complete sentences.
    """
    reduced_data = {}
    period = int(session.protocol_no.split('/')[0])
    index = int(session.protocol_no.split('/')[-1])
    reduced_data["date"] = session.date
    reduced_data["period"] = period
    reduced_data["index"] = index
    reduced_data["content"] = speeches

    return reduced_data


def mk_session(data: dict) -> namedtuple:
    Session = namedtuple('Session', ['date',
                                     'protocol_no',
                                     'period',
                                     'index',
                                     'agenda',
                                     'content'])
    for key, val in data.items():
        if key == "content":
            content = val
        elif key == "protocol_date":
            date = val
        elif key == "protocol_period":
            period = val
        elif key == "protocol_index":
            index = val
        elif key == "agenda":
            agenda = val

    protocol_no = f"{period}" + "/" + f"{index}"
    session = Session(date, protocol_no, period, index, agenda, content)

    return session


def update_session(meta: tuple, speeches: list) -> namedtuple:
    date, protocol_no, agenda = meta
    Session = namedtuple('Session', ['date',
                                     'protocol_no',
                                     'agenda',
                                     'content'])
    session = Session(date, protocol_no, agenda, speeches)

    return session


def reduce_entry_to_name(speaker: str, speaker_list: list) -> list:
    # before: 22 Hanna Musterfrau (FFF)
    # after: Hanna Musterfrau
    updated_list = []
    for entry in speaker_list:
        if speaker in entry:
            updated_list.append(speaker)
        else:
            updated_list.append(entry)

    return updated_list


def generate_agenda_topics_and_speaker_list(meta_session: tuple) -> dict:
    _, _, plan = meta_session
    agenda = {}

    for key, val in plan.items():
        topic = key
        speaker_list = val[:]
        agenda[topic] = speaker_list
        if 0:
            print(topic)
            for speaker in speaker_list:
                print(speaker)
            print()

    return agenda


def update_speeches(speech: dict,
                    speeches: list,
                    flow_indices: str,
                    current_speaker: str,
                    current_topic) -> list:

    speech[current_speaker] = flow_indices
    speech["topic"] = current_topic
    speeches.append(speech)

    return speeches


def speaker_is_in_current_lineup(speaker: str, agenda: dict, topic) -> bool:
    for name in agenda[topic]:
        if speaker in name:
            return True
    return False


def collect_speech_indices(paragraphs: list, agenda: dict) -> list:
    """
    Aim of collect_speech_indices is to collect all and only those indices of
    the paragraphs that are part of a speech.
    Interruptions like applause or questions are edited out.
    Using the speaker_list from agenda is needed to recognize if a paragraph
    is part of a speech or just a question coming from another member of
    parliament.
    This also allows to assign each speaker and his/her speech to its topic.
    """
    # initialize ######################
    speech = {}
    speeches = []
    flow_indices = []
    speakers = mk_notified_speaker_list(agenda)
    first_topic = speakers[0]
    next_topic = first_topic.split(" ;;; ")[-1]
    current_topic = next_topic  # current topic is both first and next topic
    end_of_session = False

    current_speaker = None  # first speaker will be "next" speaker in list
    speakers = speakers[1:]  # first entry was first topic

    # if topic without speakers
    if len(speakers) > 0:
        next_listed_speaker = speakers[0]
    else:
        next_listed_speaker = None

    # end of initialization ###########

    for paragraph in paragraphs:
        flow_index = paragraph['flow_index']
        speaker = paragraph['speaker_name']
        if current_speaker and speaker in current_speaker:
            # same speaker for same topic
            flow_indices.append(flow_index)
            end_of_session = False
        elif current_topic != next_topic:
            if next_listed_speaker and speaker in next_listed_speaker:
                # first speaker for new topic
                # save the indices of last speaker
                speeches = update_speeches(speech, speeches, flow_indices, current_speaker, current_topic)  # noqa

                # reset
                flow_indices = []
                speech = {}

                flow_indices.append(flow_index)
                current_topic = next_topic
                current_speaker = next_listed_speaker
                # speech[current_speaker] = []
                speakers = speakers[1:]
                if speakers:
                    next_listed_speaker = speakers[0]
                else:
                    next_listed_speaker = None
            elif next_topic and next_listed_speaker is None:
                if paragraph['speaker_is_chair']:
                    end_of_session = True
                elif speaker and speaker != current_speaker:
                    # interposing question
                    end_of_session = True
                else:
                    end_of_session = True
            elif not next_topic and not next_listed_speaker and paragraph['speaker_is_chair']:  # noqa
                end_of_session = True
        elif next_listed_speaker and speaker in next_listed_speaker:
            # new speaker for same topic
            # save the indices of last speaker - for the first speaker there
            # is no current_speaker, so this needs to be caught with "if"
            if current_speaker:
                speeches = update_speeches(speech, speeches, flow_indices, current_speaker, current_topic)  # noqa

            # reset
            flow_indices = []
            speech = {}

            current_speaker = next_listed_speaker
            flow_indices.append(flow_index)
            speakers = speakers[1:]
            if speakers:
                next_listed_speaker = speakers[0]
                if "new topic" in next_listed_speaker:
                    next_topic = next_listed_speaker.split(" ;;; ")[-1]
                    speakers = speakers[1:]
                    if speakers:
                        next_listed_speaker = speakers[0]
                    else:
                        next_listed_speaker = None
            else:
                next_listed_speaker = None
                next_topic = None
        elif next_listed_speaker and speaker not in next_listed_speaker:
            if speaker_is_in_current_lineup(speaker, agenda, current_topic):
                # weed out questions w function "is_speech"
                if is_speech(paragraph):
                    text = paragraph["speech"]
                    if is_not_interposed_question(text):
                        speeches = update_speeches(speech, speeches, flow_indices, current_speaker, current_topic)  # noqa
                        # reset
                        flow_indices = []
                        speech = {}

                        current_speaker = speaker
                        flow_indices.append(flow_index)

    if end_of_session:
        speeches = update_speeches(speech, speeches, flow_indices, current_speaker, current_topic)  # noqa

    return speeches


def is_not_interposed_question(text: str) -> bool:
    """
    To make sure that it's indeed a speech and not a question, a counter adds
    the occurences of speech elements like addressing the chair, the colleagues
    or the audience and lowering the weight if the text passage ends with a
    question mark.
    """
    counter = 0
    if text.endswith("?"):
        counter -= 1
    text = text.split()
    for i, word in enumerate(text):
        if "Herren!" in word:
            counter += 1
        elif "räsident" in word:
            counter += 1
        elif "Kolleginnen" in word:
            counter += 1

    if counter > 1:
        return True
    return False


def fill_indices_w_text(session: namedtuple, speeches: list) -> list:
    paragraphs = session.content
    updated_speech = {}
    updated_speeches = []
    token_speech = False
    token_topic = False

    for speech in speeches:
        for key, val in speech.items():
            if not key:
                continue
            elif "topic" in key:
                token_topic = True
                topic = val
            else:
                token_speech = True
                indices = val
                text = ""
                for index in indices:
                    paragraph = [p for p in paragraphs if p['flow_index'] == index][0]  # noqa
                    if is_speech(paragraph):
                        speech = paragraph['speech']
                        text = text + speech + ' '
                    elif is_citation(paragraph):
                        speech = paragraph['citation']
                        text = text + speech + ' '
                updated_speech["speaker"] = paragraph["speaker_name"]
                updated_speech["party"] = paragraph["speaker_party"]
                if paragraph["speaker_party"] is None:
                    updated_speech["ministry"] = paragraph["speaker_ministry"]
                updated_speech["content"] = text.strip()

            if token_topic and token_speech:
                updated_speech["agenda_item"] = topic
                updated_speeches.append(updated_speech)
                updated_speech = {}
                token_topic = False
                token_speech = False

    return updated_speeches


def update_speech(sentences: list, meta: tuple) -> namedtuple:
    date, protocol_no, agenda_item, speaker, party, = meta
    Speech = namedtuple('Speech', ['date',
                                   'protocol_no',
                                   'agenda_item',
                                   'speaker',
                                   'party',
                                   'speech'])
    speech = Speech(date, protocol_no, agenda_item, speaker, party, sentences)

    return speech


def walk_through_speech_indices(speech_indices: list) -> None:
    """
    The speeches as announced in the agenda lineups, but only their
    flow_indices.
    """
    print("walking through speech indices")

    for speech in speech_indices:
        print(speech)
        print()


def walk_through_speeches(speeches: list) -> None:
    print("walk through speeches")
    for speech in speeches:
        if 0:
            print()
            print(speech.date)
            print(speech.protocol_no)
            print(speech.agenda_item)
            print(speech.speaker)
            print(speech.party)
            print()
        if 0:
            for i, sent in enumerate(speech.speech):
                print(i, sent)
        if 0:
            print(speech.content)
            print()
            continue_()


def is_annotation(paragraph: dict) -> bool:
    try:
        if paragraph['annotation'] is not None:
            return True
    except KeyError:
        return False


def is_citation(paragraph: dict) -> bool:
    try:
        if paragraph['citation'] is not None:
            return True
    except KeyError:
        return False


def is_speech(paragraph: dict) -> bool:
    try:
        if paragraph['speech'] is not None:
            return True
    except KeyError:
        return False


def continue_() -> None:
    inp = input("")
    if inp == "n":
        sys.exit()


def check_occurences(description, sentences, meta, check=False) -> None:
    if not check:
        return

    funcs = {"sent_starts_w_lower_letter": first_letter_of_sent_is_lower,
             "sent_starts_w_numeral": first_letter_of_sent_is_numeric,
             "sent_starts_w_numerated_item": sent_starts_w_word_that_can_be_numerated,  # noqa
             }
    date, protocol_no, agenda_item, speaker, party = meta

    for i, sent in enumerate(sentences):
        if funcs[description](sent):
            print(protocol_no)
            print(date)
            print(agenda_item)
            print(speaker)
            print(party)
            print(i-1, sentences[i-1])
            print(i, sent)
            continue_()


def show_reconnect(index_before, index, sent_before, sent) -> None:
    print(index_before, sent_before)
    print(index, sent)
    reconnected_sent = sent_before.strip() + ' ' + sent.strip()
    print()
    print(reconnected_sent)
    print()


def mk_single_sents_in_speech(sentences: str, meta: tuple) -> list:
    if not isinstance(sentences, str):
        print(sentences)
        continue_()
    sentences = sent_tokenize(sentences, language='german')
    check_occurences("sent_starts_w_lower_letter", sentences, meta, check=False)  # noqa
    sentences = reconnect_sents_w_first_letter_is_numeric(sentences)
    check_occurences("sent_starts_w_numerated_item", sentences, meta, check=False)  # noqa
    sentences = reconnect_sents_w_first_word_can_be_numerated(sentences)
    sentences = split_sents_w_citation_start(sentences)
    sentences = split_sents_w_citation_end(sentences)
    sentences = reconnect_sents_w_lower_first_letter(sentences)
    check_occurences("sent_starts_w_numeral", sentences, meta, check=False)

    speech = update_speech(sentences, meta)
    return speech


def reconnect_sents_w_lower_first_letter(sentences: list) -> list:
    corrected_sentences = []
    token = True
    for i, sent in enumerate(sentences):
        if token and first_letter_of_sent_is_lower(sent):
            sent_before = sentences[i-1]
            if sent_before.endswith('?') or sent_before.endswith("?“ "):
                sent_before = sent_before[:-1]
            reconnected_sent = sent_before.strip() + ' ' + sent.strip()
            if len(corrected_sentences) > 0:
                del corrected_sentences[-1]
            corrected_sentences.append(reconnected_sent)
            if 0:
                show_reconnect(i-1, i, sent_before, sent)
            token = False
        else:
            corrected_sentences.append(sent)

    if not token:
        corrected_sentences = reconnect_sents_w_lower_first_letter(corrected_sentences)  # noqa

    return corrected_sentences


def split_sents_w_citation_start(sentences: list) -> list:
    corrected_sentences = []
    for i, sent in enumerate(sentences):
        if citation_start_in_sentence(sent):
            sents = sent.split(": „")
            sent_quote = sents[0] + ":"
            quote_start = "„" + sents[-1]
            corrected_sentences.append(sent_quote)
            corrected_sentences.append(quote_start)
        else:
            corrected_sentences.append(sent)

    return corrected_sentences


def split_sents_w_citation_end(sentences: list) -> list:
    corrected_sentences = []
    for i, sent in enumerate(sentences):
        if citation_end_in_sentence(sent):
            if ".“ " in sent:
                sents = sent.split(".“ ")
            else:
                sents = sent.split("?“ ")

            quote_end = sents[0] + ".“"
            new_sent = sents[-1]
            corrected_sentences.append(quote_end)
            corrected_sentences.append(new_sent)
        else:
            corrected_sentences.append(sent)

    return corrected_sentences


def citation_start_in_sentence(sent: str) -> bool:
    if ": „" in sent:
        return True
    return False


def citation_end_in_sentence(sent: str) -> bool:
    if ".“ " in sent:
        return True
    elif "?“ " in sent:
        return True
    return False


def first_letter_of_sent_is_lower(sent: str) -> bool:
    # if sent.startswith('…'):
    #     return False
    for c in sent:
        if c.isnumeric():
            return False
        elif c.isalpha():
            return c.islower()

    return False


def first_letter_of_sent_is_numeric(sent: str) -> bool:
    for c in sent:
        if c.isnumeric():
            return True
        elif c.isalpha():
            return False

    return False


def sent_ends_w_abbr(sent: str) -> bool:
    abbreviations = ["ca.", "Art.", "Co."]
    end_of_sent = sent.split()[-1]
    if end_of_sent in abbreviations:
        return True
    return False


def reconnect_sents_w_first_letter_is_numeric(sentences: list) -> list:
    corrected_sentences = []
    token = True
    for i, sent in enumerate(sentences):
        if first_letter_of_sent_is_numeric(sent):
            sent_before = sentences[i-1]
            if token and sent_before and sent_ends_w_abbr(sent_before):
                reconnected_sent = sent_before.strip() + ' ' + sent.strip()
                del corrected_sentences[-1]
                corrected_sentences.append(reconnected_sent)
                if 0:
                    show_reconnect(i-1, i, sent_before, sent)
                token = False
            else:
                corrected_sentences.append(sent)
        else:
            corrected_sentences.append(sent)

    if not token:
        corrected_sentences = reconnect_sents_w_first_letter_is_numeric(corrected_sentences)  # noqa

    return corrected_sentences


def sent_ends_w_comma(sent: str) -> bool:
    if sent.strip().endswith(","):
        return True
    return False


def sent_before_ends_w_period(sent: str) -> bool:
    end_of_sent = sent[-1]
    if end_of_sent == '.':
        return True
    return False


def sent_starts_w_word_that_can_be_numerated(sent: str) -> bool:
    words_that_can_be_numerated = ["Band", "Band,",
                                   "Absatz", "Abschnitt",
                                   "Absatz,", "Abschnitt,",
                                   "Kapitel", "Kapitel,",
                                   "Jahr", "Jahr,",
                                   "Wahlperiode", "Wahlperiode,",
                                   "Wahlperiode.",
                                   "Sitzung", "Sitzung,",
                                   "Tag", "Tag,",
                                   "Landtag", "Landtag,", "Landtags",
                                   "Landtages",
                                   ]
    first_word = sent.strip().split()[0]
    if first_word in words_that_can_be_numerated:
        return True
    return False


def sent_ends_with_number(sent: str) -> bool:
    last_word = sent.split()[-1]
    if last_word.endswith("."):
        last_word = last_word[:-1]
    if last_word.isnumeric():
        return True
    return False


def reconnect_sents_w_first_word_can_be_numerated(sentences: list) -> list:
    corrected_sentences = []
    token = True
    for i, sent in enumerate(sentences):
        if sent_starts_w_word_that_can_be_numerated(sent):
            sent_before = sentences[i-1]
            if token and sent_ends_with_number(sent_before):
                reconnected_sent = sent_before.strip() + ' ' + sent.strip()
                del corrected_sentences[-1]
                corrected_sentences.append(reconnected_sent)
                if 0:
                    show_reconnect(i-1, i, sent_before, sent)
                token = False
            else:
                corrected_sentences.append(sent)
        else:
            corrected_sentences.append(sent)

    if not token:
        corrected_sentences = reconnect_sents_w_first_word_can_be_numerated(corrected_sentences)  # noqa

    return corrected_sentences


def mk_correct_single_sents(speeches: list, date: str, protocol_no: str) -> list:  # noqa
    speeches_w_corrected_sents = []
    for speech in speeches:
        speaker = None
        party = None
        text = None
        topic = None
        for key, val in speech.items():
            if key == "content":
                text = val
            elif key == "speaker":
                speaker = val
            elif key == "party":
                party = val
            elif key == "agenda_item":
                topic = val
            elif key == "ministry":
                ministry = val
            if text and speaker and topic:
                if party is None:
                    party = ministry
                meta = (date, protocol_no, topic, speaker, party)

                # using nltk and correcting nltk errors
                speech = mk_single_sents_in_speech(text, meta)
                speeches_w_corrected_sents.append(speech)

    return speeches_w_corrected_sents


def save_json_protocol(period, index, protocol):

    """ Save protocol data to JSON file for period and index.
    """
    filename = os.path.join(
        NLTK_DIR,
        PROTOCOL_FILE_TEMPLATE % (period, index, 'json'))
    json.dump(protocol, open(filename, 'w', encoding='utf-8'))


def process_single_json_file(period, index) -> None:
    data = load_json_file(period, index)
    if 0:
        walk_through_original_data(data)
    collect_speeches_w_whole_sents(data)


def collect_speeches_w_whole_sents(data: dict) -> None:
    if 0:
        walk_through_original_data(data)
        continue_()

    session = mk_session(data)
    date, protocol_no, agenda = session.date, session.protocol_no, session.agenda  # noqa
    paragraphs = session.content
    speech_indices = collect_speech_indices(paragraphs, agenda)
    if 0:
        walk_through_speech_indices(speech_indices)
        continue_()

    speeches = fill_indices_w_text(session, speech_indices)
    speeches_w_corrected_sents = mk_correct_single_sents(speeches, date, protocol_no)  # noqa
    if 0:
        walk_through_speeches(speeches_w_corrected_sents)
        continue_()

    final_session = complete_session(session, speeches_w_corrected_sents)
    if 1:
        walk_through_updated_data(final_session)

    return final_session


def process_whole_period(period) -> None:
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
        session_data = load_json_file(period, index)
        final_session = collect_speeches_w_whole_sents(session_data)
        # print("save?")
        # continue_()
        save_json_protocol(period, index, final_session)


def main():
    period = int(sys.argv[1])
    if len(sys.argv) > 2:
        index = int(sys.argv[2])
        process_single_json_file(period, index)
    else:
        process_whole_period(period)


if __name__ == "__main__":
    main()
