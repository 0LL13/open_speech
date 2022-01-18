#!/usr/bin/env python3
"""
Find the session agenda and the list of speakers announced to speak.
The result should look like this:
    - agenda item number (1, 2, ...)
    - agenda item description
    - agenda item list of speakers
The end of the agenda is reached when there is the item "Entschuldigt
waren ..." or the start of the session "Beginn ..."

When imported use function "mk_agenda_list_w_speakers(period, index)" to get
the agenda (will be dict).
I tried to do the processing of the html files like Marc did and named the
functions accordingly.
"""
import bs4
import os
import re
import sys

from parse_data import create_parser
from parse_data import clean_tag_text
from settings import (
    PROTOCOL_DIR,
    PROTOCOL_FILE_TEMPLATE,
    )


# RE for find_start() actually ENDS the agenda!
BEGIN_RE = re.compile(r'Beginn:|Beginn \d\d[:\.]\d\d|Seite 3427')
# RE for attachments
ATTACHMENT_RE = re.compile(r'Anlage \w*')
# RE for either only a number or a number and agenda item
RE_AGENDA_ITEM = re.compile(r'^\d+[^\/^.^:]*\w+$')

# RE for member of parliament (name + party) or minister
NAME_DEF = r'[^Gesetz][\w\-‑.’\' ]+'
PARTY_RE = r'\([ACDEfFGINPRSTUÜ]*\)|\(fraktionslos\)'
PAGE_NO_RE = r'\d*'
MOP_RE = re.compile(NAME_DEF + PARTY_RE + PAGE_NO_RE)
MINISTER_RE = re.compile('((?:geschäftsführender? )?minister(?:in)?) (.+)', re.I)  # noqa

# RE for results and absent
RESULT_RE = re.compile(r'Ergebnis[\.]*', re.I)
ABSENT_RE = re.compile(r'Entschuldigt[\w]*', re.I)

# parties
PARTIES = ["(AfD)", "(CDU)", "(FDP)", "(GRÜNE)", "(PIRATEN)", "(SPD)",
           "(fraktionslos)"]


def find_agenda_start(soup: bs4.BeautifulSoup) -> bs4.element.Tag:
    """
    Special cases:
        - "Regierungserklärung" (16/7)
        - no speeches (16/10)
        - only one TOP without number (17/138)
        - only one TOP with number (17/139)
    """
    agenda_end_index = find_agenda_end(soup)
    paragraphs = soup.find_all('p')[:agenda_end_index]

    for i, p in enumerate(paragraphs):
        if p.text.split() and p.text.split()[0] == "1":
            agenda_start = p
            return agenda_start

    for i, p in enumerate(paragraphs):
        if "Regierungserklärung" in p.text:
            agenda_start = p
            return agenda_start

    # if no agenda start was found, try without number:
    agenda_start = find_agenda_start_wo_number(paragraphs)
    return agenda_start


def find_agenda_end(soup: bs4.BeautifulSoup) -> int:
    paragraphs = soup.find_all('p')
    for i, p in enumerate(paragraphs):
        if "Anlage" in p.text and "siehe Anlage" not in p.text:
            return i
        elif "Entschuldigt" in p.text:
            return i
        elif "Beginn:" in p.text:
            return i

    print("Did not find proper ending for agenda, return default index: 30")
    return 30


def find_agenda_start_wo_number(paragraphs: list) -> bs4.element.Tag:  # noqa
    classes_w_agenda_items = ["MsoToc9", "MsoToc7", "MsoToc1"]
    for p in paragraphs:
        try:
            class_ = p['class'][0]
            if class_ in classes_w_agenda_items:
                agenda_start = p
                # print("found agenda start wo number:", agenda_start)
                return agenda_start
        except KeyError:
            pass

    print("Did not find agenda start wo number")
    continue_()


def is_numbered_agenda_item(text: str) -> bool:
    CHARS_TO_REMOVE = [':', '-', '!', '?', '„', '“', ',', '–', '.']
    items = text.split()
    try:
        agenda_no = items[0]
        if agenda_no.isnumeric():
            if int(agenda_no) <= 99:
                try:
                    topic = items[1]
                    # https://stackoverflow.com/a/10017169/6597765
                    rx = '[' + re.escape(''.join(CHARS_TO_REMOVE)) + ']'
                    topic = re.sub(rx, '', topic)
                    if topic.isalpha():
                        return True
                    elif topic.isnumeric():
                        topic = items[2]
                        if topic.isalpha():
                            return True
                except (IndexError):
                    pass
    except IndexError:
        pass
    return False


def process_protocol(html_filename: str) -> dict:
    # Parse file
    soup = create_parser(html_filename)
    agenda = parse_agenda(soup)

    if 1:
        print("process protocol")
        print()
        for key, val in agenda.items():
            print(f"{key}:\n{val}")
            print()

    return agenda


def mk_html_filename(period=None, index=None) -> str:
    if period is None:
        period = int(sys.argv[1])
    if index is None:
        index = int(sys.argv[2])
    html_filename = os.path.join(
        PROTOCOL_DIR,
        PROTOCOL_FILE_TEMPLATE % (period, index, 'html'))
    return html_filename


def parse_agenda(soup: bs4.BeautifulSoup) -> dict:
    session_agenda = {}
    speakers = []
    actual_key = None
    found_agenda_item = False
    agenda_start = find_agenda_start(soup)
    # print("agenda_start:", agenda_start)
    agenda_start_text = clean_tag_text(agenda_start)

    if agenda_start:
        if 0:
            print("item:", agenda_start_text)
            print("agenda_start:", agenda_start)
        actual_key = agenda_start_text
        found_agenda_item = True
        session_agenda[actual_key] = speakers
    else:
        print("no agenda found!")
        continue_()
        return None

    for tag in agenda_start.find_all_next('p'):
        if 0:
            print("agenda:")
            print(session_agenda)
            continue_()
        tag_text = clean_tag_text(tag)
        # print("tag_text:", tag_text)
        if not tag_text:
            continue

        match_speaker_mop = MOP_RE.match(tag_text)
        match_result = RESULT_RE.match(tag_text)
        match_absent = ABSENT_RE.match(tag_text)
        match_begin = BEGIN_RE.match(tag_text)
        match_attachment = ATTACHMENT_RE.match(tag_text)

        if is_numbered_agenda_item(tag_text):
            found_agenda_item = True
            if actual_key is not None:
                actual_key = tag_text
                speakers = []
                session_agenda[actual_key] = speakers
            else:
                actual_key = tag_text
                session_agenda[actual_key] = speakers
        elif found_agenda_item and "inister" in tag_text:
            if "konferenz" not in tag_text and "Einzelplan" not in tag_text:
                # print("tag_text:", tag_text)
                speakers.append(tag_text)
        elif found_agenda_item and match_speaker_mop:
            # print("tag_text:", tag_text)
            if "Abgeordneten" not in tag_text and "Einzelplan" not in tag_text:  # noqa
                speakers.append(tag_text)
        elif found_agenda_item and match_result:
            pass
        elif match_absent:
            break
        elif match_begin:
            break
        elif match_attachment:
            break
        elif found_agenda_item and tag_text.split()[-1].isnumeric():
            words = tag_text.split()[:-1]
            if words and words[-1] in PARTIES:
                # print("mop that wasnt caught by RE:", tag_text)
                speakers.append(tag_text)

    if 0:
        print("parse agenda")
        print()
        for key, val in session_agenda.items():
            print(f"{key}:\n{val}")
            print()

    return session_agenda


def parse_agenda_wo_numbers(soup: bs4.BeautifulSoup) -> dict:
    session_agenda = {}
    speakers = []
    agenda_start = find_agenda_start_wo_number(soup)
    agenda_start_text = clean_tag_text(agenda_start)
    only_item = agenda_start_text  # no numbering means that there is only one item  # noqa

    for tag in agenda_start.find_all_next('p'):
        # print(session_agenda)
        tag_text = clean_tag_text(tag)
        # print("tag_text:", tag_text)
        if not tag_text:
            continue
        match_speaker_mop = MOP_RE.match(tag_text)
        match_result = RESULT_RE.match(tag_text)
        match_begin = BEGIN_RE.match(tag_text)
        match_absent = ABSENT_RE.match(tag_text)
        match_attachment = ATTACHMENT_RE.match(tag_text)

        if "inister" in tag_text and "konferenz" not in tag_text:
            speakers.append(tag_text)
        elif match_speaker_mop and "Abgeordneten" not in tag_text:  # noqa
            speakers.append(tag_text)
        elif match_result:
            pass
        elif match_absent:
            break
        elif match_begin:
            break
        elif match_attachment:
            # no more speeches (except written statements)
            break

    session_agenda[only_item] = speakers

    if 0:
        for key, val in session_agenda.items():
            print(f"{key}:\n{val}")
            print()

    return session_agenda


def mk_agenda_list_w_speakers(period: str, index: str) -> dict:
    html_filename = mk_html_filename(period, index)
    agenda = process_protocol(html_filename)

    return agenda


def continue_() -> None:
    inp = input("")
    if inp == "n":
        sys.exit()


if __name__ == "__main__":
    html_filename = mk_html_filename()
    process_protocol(html_filename)
