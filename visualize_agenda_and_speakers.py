#!/usr/bin/env python3
"""
Visualize agenda and speakers.
"""
import json
import os
import sys

from collections import namedtuple

from agenda_and_speaker_list import mk_agenda_list_w_speakers
from settings import (
    PROTOCOL_DIR,
    PROTOCOL_FILE_TEMPLATE,
    )


def continue_() -> None:
    inp = input("")
    if inp == "n":
        sys.exit()


def load_json_file(period: str, index: str) -> dict:
    """
    Marc's loading function using a template.
    """
    json_filename = os.path.join(
        PROTOCOL_DIR,
        PROTOCOL_FILE_TEMPLATE % (period, index, 'json'))

    with open(json_filename) as json_file:
        data = json.load(json_file)

    agenda = mk_agenda_list_w_speakers(period, index)
    data["agenda"] = agenda
    return data


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


def agenda_topics_and_speaker_list(meta_session: tuple,
                                   show: bool = False) -> dict:
    """
    Make a dictionary with topics as keys and lineup of speakers as value.
    Show if requested.
    """
    date, protocol_no, plan = meta_session
    agenda = {}

    if show:
        print("date:", date)
        print("protocol_no:", protocol_no)
        continue_()

    for key, val in plan.items():
        topic = key
        speaker_list = val[:]
        agenda[topic] = speaker_list
        if show:
            print("New topic:", end=" ")
            print(topic)
            for speaker in speaker_list:
                print(speaker)
            print()

    return agenda


def visualize_speaker_flow(session: namedtuple) -> None:
    """
    Show the actual speech action.
    """

    paragraphs = session.content
    current_speaker = None

    for paragraph in paragraphs:
        flow_index = paragraph['flow_index']
        speaker = paragraph['speaker_name']
        if speaker == current_speaker:
            print(".", end="")
        elif paragraph['speaker_is_chair']:
            print()
            print(f'chair - flow_index: {flow_index}', end=" ")
            current_speaker = speaker
        else:
            print()
            new_speaker = speaker
            print(f'{new_speaker} - flow_index: {flow_index}', end=" ")
            current_speaker = new_speaker


def mk_notified_speaker_list(agenda: dict) -> list:
    speakers = []
    for key, val in agenda.items():
        speakers.append(f"new topic ;;; {key}")
        speaker_list = val
        for speaker in speaker_list:
            speakers.append(speaker)

    return speakers


def reduce_speaker_flow_to_notified_speakers(session: namedtuple,
                                             speakers: list) -> None:

    paragraphs = session.content
    new_topic = speakers[0]
    current_speaker = None

    new_topic = new_topic.split(" ;;; ")[-1]
    speakers = speakers[1:]

    # if topic without speakers
    if len(speakers) > 0:
        next_listed_speaker = speakers[0]
    else:
        next_listed_speaker = None

    print(new_topic)
    print(speakers)
    current_topic = new_topic

    for paragraph in paragraphs:
        flow_index = paragraph['flow_index']
        speaker = paragraph['speaker_name']
        if current_speaker and speaker in current_speaker:
            print(f"{flow_index}", end=" ")
        elif current_topic != new_topic:
            if next_listed_speaker and speaker in next_listed_speaker:
                # first speaker for new topic
                print()
                print()
                print(new_topic)
                current_topic = new_topic
                print()
                print(f'{speaker} - flow_index: {flow_index}', end=" ")
                current_speaker = next_listed_speaker
                speakers = speakers[1:]
                if speakers:
                    next_listed_speaker = speakers[0]
                else:
                    next_listed_speaker = None
        elif next_listed_speaker and speaker in next_listed_speaker:
            # new speaker for same topic
            print()
            print(f'{speaker} - flow_index: {flow_index}', end=" ")
            current_speaker = next_listed_speaker
            speakers = speakers[1:]
            if speakers:
                next_listed_speaker = speakers[0]
                if "new topic" in next_listed_speaker:
                    new_topic = next_listed_speaker.split(" ;;; ")[-1]
                    speakers = speakers[1:]
                    if speakers:
                        next_listed_speaker = speakers[0]
                    else:
                        next_listed_speaker = None
            else:
                next_listed_speaker = None

    print()


def process_single_json_file(period, index) -> None:
    data = load_json_file(period, index)
    session = mk_session(data)
    meta_session = (session.date, session.protocol_no, session.agenda)
    agenda = agenda_topics_and_speaker_list(meta_session, show=False)
    notified_speakers = mk_notified_speaker_list(agenda)

    if 1:
        agenda_topics_and_speaker_list(meta_session, show=True)
        continue_()

    if 1:
        visualize_speaker_flow(session)
        print()
        continue_()

    if 1:
        reduce_speaker_flow_to_notified_speakers(session, notified_speakers)


def main():
    period = int(sys.argv[1])
    if len(sys.argv) > 2:
        index = int(sys.argv[2])
        process_single_json_file(period, index)
    else:
        print("Needs arguments for legislature period and protocol index!")


if __name__ == "__main__":
    main()
