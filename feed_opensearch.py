#!/usr/bin/env python3
"""
    Load parsed JSON of session protocols into OpenSearch.

    Written by Marc-Andre Lemburg, Nov 2021

"""
import sys
import os
import json

# It would be better to use ES Python client, since this is more
# up-to-date than the OpenSearch one, but the ES client fails with an
# error: elasticsearch.exceptions.UnsupportedProductError: The client
# noticed that the server is not Elasticsearch and we do not support
# this unknown product when connecting to an OpenSearch instance.
#
#   import elasticsearch as opensearchpy
#   import elasticsearch.helpers as opensearchpy_helpers
#   opensearchpy.helpers = opensearchpy_helpers
#   opensearchpy.OpenSearch = opensearchpy.Elasticsearch
import opensearchpy
import opensearchpy.helpers
import sys

import load_data
from settings import (
    PROTOCOL_DIR,
    PROTOCOL_FILE_TEMPLATE,
    OPENSEARCH_HOSTS,
    OPENSEARCH_AUTH,
    )

### Globals

# Name of the main index in OS
INDEX_NAME = 'nrw_landtag_protocols'

# Index template to use
INDEX_TEMPLATE = json.dumps({
    'index_patterns': [INDEX_NAME],
    'template': {
        'mappings': {
            'properties': {
                'protocol_date': { 'type': 'date' },
                'protocol_title': { 'type': 'text' },
                'protocol_period': { 'type': 'integer' },
                'protocol_index': { 'type': 'integer' },
                'protocol_url': { 'type': 'url' },
                'speaker_name': { 'type': 'keyword' },
                'speaker_party': { 'type': 'keyword' },
                'speaker_ministry': { 'type': 'keyword' },
                'speaker_role': { 'type': 'keyword' },
                'speaker_role_descr': { 'type': 'keyword' },
                'speaker_is_chair': { 'type': 'boolean' },
                'speech': { 'type': 'text' },
                'annotation': { 'type': 'text' },
                'citation': { 'type': 'text' },
                'html_class': { 'type': 'keyword' },
                'flow_index': { 'type': 'integer' },
                'speaker_flow_index': { 'type': 'integer' },
            }
        }
    }
})

# Verbosity
verbose = 0

###

def load_json_protocol(period, index):

    """ Load the JSON dump of the parsed protocol for period and index.

    """
    filename = os.path.join(
        PROTOCOL_DIR,
        PROTOCOL_FILE_TEMPLATE % (period, index, 'json'))
    data = json.load(open(filename, 'r', encoding='utf-8'))
    return data

def bulk_insert_generator(protocol, index_name):

    """ Generator for inserting protocol paragraphs into OS

        The paragraphs will be inserted into the index index_name and
        use the ID "p-<period>-<index>-<flow_index>", so that repeated
        loads will create new versions in OS.

    """
    content = protocol['content']
    global_attributes = {}
    for k,v in protocol.items():
        if k == 'content':
            continue
        global_attributes[k] = v
    period = protocol['protocol_period']
    index = protocol['protocol_index']
    for paragraph in content:
        # Add additional global attributes
        data = {
            '_op_type': 'index',
            '_index': index_name,
            '_id': 'p-%i-%i-%i' % (period, index, paragraph['flow_index']),
            **global_attributes,
            **paragraph,
        }
        yield data

def opensearch_client():

    """ Return an open OS client connection

    """
    client = opensearchpy.OpenSearch(
        hosts=OPENSEARCH_HOSTS,
        http_auth=OPENSEARCH_AUTH.split(':'),
        http_compress=True,
        use_ssl=True,
        verify_certs=False,
        ssl_show_warn=False,
        # Other settings such as SSL could go here
    )
    return client

def process_protocol(period, index, os_index_name=INDEX_NAME):

    """ Load paragraphs of protocol period-index into OS

        The loading is done using 'index' and all paragraphs are indexed
        using p-<period>-<index>-<flow_index>, so that repeated loads
        will create new versions in OS.

    """
    with opensearch_client() as client:
        protocol = load_json_protocol(period, index)
        # Create/update an index template for the index, which provides the
        # mappings to be used for the index
        client.indices.put_template(
            name=os_index_name,
            body=INDEX_TEMPLATE,
        )
        for result in opensearchpy.helpers.streaming_bulk(
                client,
                bulk_insert_generator(protocol, index_name=os_index_name),
            ):
            if verbose > 1:
                print (f'Result from OS insert: {result}')

def main():

    period = int(sys.argv[1])
    if len(sys.argv) > 2:
        # Process just one protocl
        index = int(sys.argv[2])
        process_protocol(period, index)
    else:
        # Process all available documents
        data = load_data.load_period_data(period)
        for filename, protocol in sorted(data.items()):
            if os.path.splitext(filename)[1] != '.html':
                continue
            index = protocol['index']
            print ('-' * 72)
            print (f'Feeding protocol {period}-{index} to OpenSearch')
            process_protocol(period, index)

###

if __name__ == '__main__':
    main()
