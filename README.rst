Overview
========

:license:
    .. image:: https://img.shields.io/github/license/0LL13/open_speech?style=plastic
        :alt: GitHub

:version:
    .. image:: https://img.shields.io/github/pipenv/locked/python-version/0LL13/open_speech?style=plastic
        :alt: GitHub Pipenv locked Python version


Make NRW parliament speeches available in text format (from HTML).
Do some speech analysis like sentiment analysis or summarization.


Features
--------

- Parse NRW parliament debates using the parser written by Marc-André Lemburg.
- Extract agenda of each session and speaker lineup.
- Collect speeches without any interruptions like applause or questions.
- Tag speeches with date, protocol number, speaker's name and party (or
  ministry), and the topic as found in the agenda.
- Tokenize speeches into single sentences with nltk, correct blunders.
- Analyse sentiments of sentences using german-sentiment-bert.
- Summarize speeches using extractive method.


Usage
-----
::



Credits
-------

Marc-André Lemburg wrote the parser:
GitHub repo: https://github.com/malemburg/nrw-landtag-protocols


Installation
------------
::



Contribute
----------



Support
-------



Planned
-------



Warranty
--------

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE, TITLE AND NON-INFRINGEMENT. IN NO EVENT SHALL
THE COPYRIGHT HOLDERS OR ANYONE DISTRIBUTING THE SOFTWARE BE LIABLE FOR ANY
DAMAGES OR OTHER LIABILITY, WHETHER IN CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
IN THE SOFTWARE.

In this particular package this means especially that there is no warranty
concerning the completeness of degrees for a country, the proper spelling of
the degrees listed, and the correctness of those degrees.


License
-------

MIT License

Copyright (c) 2021 Oliver Stapel
