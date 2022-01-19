""" Global settings used by the parsers

"""
import os
import pwd


def get_username():
    username = pwd.getpwuid(os.getuid())[0]
    return username


# Base URL to use for fetching data
BASE_URL = 'https://www.landtag.nrw.de/portal/WWW/dokumentenarchiv/Dokument/'

# Protocol storage
PROTOCOL_DIR = 'protocols'
PROTOCOL_FILE_TEMPLATE = 'protocol-%i-%i.%s'
NLTK_DIR = os.path.join(PROTOCOL_DIR, 'nltk')
BERT_DIR = os.path.join(PROTOCOL_DIR, 'bert')
TAGGER_DIR = os.path.join(PROTOCOL_DIR, 'tagger')
username = get_username()
TREETAGGER_DIR = f'/home/{username}/nltk_data/tree_tagger'

# Period download data
PERIOD_FILE_TEMPLATE = 'period-%i.json'

# Max. number of download failures
MAX_FAILURES = 10

# ## OpenSearch

# Hosts to connect to
OPENSEARCH_HOSTS = [
    {'host': 'localhost', 'port': 9200},
]

# Login for OS in the format userid:password
OPENSEARCH_AUTH = os.environ.get('OPENSEARCH_AUTH', 'admin:admin')
