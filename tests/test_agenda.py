#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for agenda_and_speaker_list.py"""
from context import mk_agenda_list_w_speakers


def test_agenda_is_dict():
    period = 16
    index = 24
    agenda = mk_agenda_list_w_speakers(period, index)
    assert isinstance(agenda, dict)


def test_agenda_has_one_item_wo_numbering():
    period = 17
    index = 138
    agenda = mk_agenda_list_w_speakers(period, index)
    assert len(agenda) == 1
    for k, v in agenda.items():
        assert k[0].isalpha()


def test_agenda_has_one_item_w_numbering():
    period = 17
    index = 139
    agenda = mk_agenda_list_w_speakers(period, index)
    assert len(agenda) == 1
    for k, v in agenda.items():
        assert k[0].isnumeric()
