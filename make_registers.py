import os
import math
import requests
import re
import xml.sax as sax
from xml.etree import cElementTree
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
from time import sleep
import logging
import sys

logger = logging.getLogger('make_registers')

DEBUG = True

# Define the number of records to retrieve per CSW query page
RECORDS_PER_PAGE = 1000

# Define the number of times to retry a failed query
MAX_QUERY_RETRIES = 1

# Define number of seconds to sleep before retrying failed query
RETRY_SLEEP_SECONDS = 5

# Define number of seconds to wait for query response
QUERY_TIMEOUT = 120

DATASET_CSW_URL = 'https://ecat.ga.gov.au/geonetwork/srv/eng/csw'
DATASET_XML = 'datasets.xml'
DATASET_URI_BASE = 'http://pid.geoscience.gov.au/dataset/'
DATASET_IDS = 'datasets.txt1'
DATASET_URIS = 'datasets.txt'
SERVICE_CSW_URL = 'https://ecat.ga.gov.au/geonetwork/srv/eng/csw'
SERVICE_XML = 'services.xml'
SERVICE_URI_BASE = 'http://pid.geoscience.gov.au/service/'
SERVICE_URIS = 'services.txt'
STATIC_DIR = 'http://13.54.73.187/static'

def store_csw_request(csw_endpoint, request_xml, xml_file_to_save):
    r = requests.post(csw_endpoint,
                      data=request_xml,
                      headers={'Content-Type': 'application/xml'},
                      stream=True)

    with open(xml_file_to_save, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)
    return True


# TODO: implement this to process the requests request as a stream straight into SAX
def stream_csw_request(csw_endpoint, request_xml):
    r = requests.post(csw_endpoint,
                      data=request_xml,
                      headers={'Content-Type': 'application/xml'},
                      timeout=QUERY_TIMEOUT,
                      stream=True)
    assert r.status_code == 200, 'status_code = {}'.format(r.status_code)
    #assert not re.findall('Catalog is indexing records', r.content.decode('utf-8')), 'Catalog is indexing records'
    return r.raw


def make_csw_request_xml(start_position, max_records, record_type='dataset', ElementSetName='full'):
    xml_template_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'templates',
        'csw_request_records.xml')
    xml = open(xml_template_path, 'r').read()
    xml = xml.replace('{{ start_position }}', str(start_position))
    xml = xml.replace('{{ max_records }}', str(max_records))
    xml = xml.replace('{{ record_type }}', str(record_type))
    xml = xml.replace('{{ ElementSetName }}', str(ElementSetName))
    logger.debug(xml)
    return xml


def get_total_no_of_records(csw_endpoint, record_type='dataset'):
    xml_template_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'templates',
        'csw_request_count.xml')
    xml = open(xml_template_path, 'r').read()
    xml = xml.replace('{{ record_type }}', str(record_type))
    logger.debug(xml)
    xml = xml.encode('utf-8')

    retries = 0
    while retries <= MAX_QUERY_RETRIES:
        r = requests.post(csw_endpoint,
                          data=xml,
                          headers={'Content-Type': 'application/xml'},
                          timeout=QUERY_TIMEOUT)
    
        # extract the number of hits
        #return r.content
        logger.debug(r.content.decode('utf-8'))
        try:
            assert r.status_code == 200, 'status_code = {}'.format(r.status_code)
            return int(re.findall('numberOfRecordsMatched="(\d+)"', r.content.decode('utf-8'))[0])
        except Exception as e:
            logger.warning('Record count query failed: {}'.format(e))
            retries += 1
            sleep(RETRY_SLEEP_SECONDS)
            logger.info('Retrying...')
            
    raise Exception('Maximum number of retries exceeded for record count query')

class IdHandler(sax.ContentHandler):
    # see http://python.zirael.org/e-sax2.html
    def __init__(self):
        sax.ContentHandler.__init__(self)
        self.ids = []
        self.one = False
        self.two = False
        self.three = False
        self.four = False
        self.five = False
        self.six = False
        self.seven = False
        self.parent = []

    # check for a particular sequence of tags:
    # identificationInfo SV_ServiceIdentification citation CI_Citation identifier RS_Identifier code CharacterString
    # this is similar to an XPath query but this function notices every start tag, not just those in the hierarchy
    # above, also anything else in between
    def startElementNS(self, name, qname, attrs):
        uri, localname = name
        # //mdb:MD_Metadata/mdb:alternativeMetadataReference/cit:CI_Citation/cit:identifier/mcc:MD_Identifier/mcc:code/gco:CharacterString/text()
        if localname == 'MD_Metadata':
            self.one = True
        if self.one and localname == 'alternativeMetadataReference':
            self.two = True
        if self.two and localname == 'CI_Citation':
            self.three = True
        if self.three and localname == 'identifier':
            self.four = True
        if self.four and localname == 'MD_Identifier':
            self.five = True
        if self.five and localname == 'code':
            self.six = True
        if self.six and localname == 'CharacterString':
            self.seven = True

    # if the required sequence of start tags is true (all 7 flags are True), record the content
    def characters(self, content):
        if self.one and self.two and self.three and self.four and self.five and self.six and self.seven:
            try:
                self.ids.append(int(content))
            except Exception:
                pass

    # once an eCat ID has been found, reset the stream checker
    def endElementNS(self, name, qname):
        if self.one and self.two and self.three and self.four and self.five and self.six and self.seven:
            self.one = False
            self.two = False
            self.three = False
            self.four = False
            self.five = False
            self.six = False
            self.seven = False


def extract_ecat_ids(csw_result_file):
    n = IdHandler()
    parser = sax.make_parser()
    parser.setContentHandler(n)
    parser.setFeature(sax.handler.feature_namespaces, True)
    parser.parse(open(csw_result_file, 'r'))

    return sorted(n.ids)


def extract_ecat_ids_stream(result_stream):
    n = IdHandler()
    parser = sax.make_parser()
    parser.setContentHandler(n)
    parser.setFeature(sax.handler.feature_namespaces, True)
    parser.parse(result_stream)

    return sorted(n.ids)

def get_ecat_ids(csw_endpoint, record_type='dataset'):
    '''
    Function to return sorted list of eCat IDs using paginated CSW queries
    '''
    num_records = get_total_no_of_records(csw_endpoint, record_type=record_type)
    #num_records = 3000
    logger.info('Total number of {} records to retrieve: {}'.format(record_type, num_records))

    # calculate the total number of page calls
    no_pages = int(math.ceil(num_records / RECORDS_PER_PAGE))

    # paginate the response until no_page_calls reached, adding result of each page request to ids list
    ids = []
    page = 1
    while page <= no_pages:
        start_position = (page - 1) * RECORDS_PER_PAGE + 1
        paged_query = make_csw_request_xml(start_position, RECORDS_PER_PAGE, record_type=record_type)
        # request one page
        logger.info('requesting page {} of {}'.format(page, no_pages))
        retries = 0
        while True: # Loop for query retries on failure
            try:
                i = extract_ecat_ids_stream(stream_csw_request(DATASET_CSW_URL, paged_query))
                logger.debug(i)
                logger.info('page ids: {}'.format(len(i)))
                ids.extend(i)        
                page += 1
                break
            except Exception as e:
                logger.warning('Query failed: '.format(e))
                if retries < MAX_QUERY_RETRIES:
                    retries += 1
                    sleep(RETRY_SLEEP_SECONDS)
                    logger.info('Retrying...')
                else:
                    raise Exception('Maximum number of retries exceeded')

    ids.sort()  # to sort the entire lists, since it is paginated
    logger.debug(ids)
    logger.info('total: {}'.format(len(ids)))

    return ids


# incomplete ET implementation of the same SAX parsing as IdHandler
def extract_ecat_ids_et(xml_file):
    context = cElementTree.iterparse(open(xml_file), events=('start', 'end'))
    context = iter(context)
    event, root = context.next()

    # for event, elem in context:
    #     if elem.tag == 'CharacterString':
    #         print(elem.tag)
    #         elem.clear()
    #         root.clear()

    events = ('start', 'start-ns')
    ns_map = []
    for event, elem in cElementTree.iterparse(open(xml_file), events=events):
        if event == 'start-ns':
            ns_map.append(elem)

        elif event == 'start':
            if root is None:
                root = elem
            for prefix, uri in ns_map:
                elem.set('xmlns:' + prefix, uri)
            local_name = elem.tag.split('}')[1]

            if local_name == 'CharacterString':
                print(elem.text)
            ns_map = []


def generate_register(ecat_ids, datasets_services='datasets', mime='text/html', html_static_dir=''):
    if mime == 'text/html':
        # render a Jinja2 template after telling it where the templates dir is
        template = Environment(loader=FileSystemLoader(os.path.dirname(os.path.realpath(__file__)) + '/templates'))\
            .from_string(open(os.path.dirname(os.path.realpath(__file__)) + '/templates/{}.html'
                              .format(datasets_services)).read())
        return template.render(ids=ecat_ids, static=html_static_dir)
    elif mime == 'text/turtle':
        # render a Jinja2 template after telling it where the templates dir is
        template = Environment(loader=FileSystemLoader(os.path.dirname(os.path.realpath(__file__)) + '/templates'))\
            .from_string(open(os.path.dirname(os.path.realpath(__file__)) + '/templates/{}.ttl'
                              .format(datasets_services)).read())
        return template.render(ids=ecat_ids)
    else:
        raise ValueError('\'mime\' must be either text/html or text/turtle. Default (None) is text/html.')


def main():

    #
    #   Services
    #
    # get all the service IDs from eCat's Service's virtual CSW endpoint
    service_ids = get_ecat_ids(SERVICE_CSW_URL, record_type='service')
   
    # make an HTML & a TTL file from those IDs
    open(os.path.dirname(os.path.realpath(__file__)) + '/services.html', 'w').write(generate_register(
        service_ids,
        datasets_services='services',
        mime='text/html',
        html_static_dir=STATIC_DIR
    ))
   
    open(os.path.dirname(os.path.realpath(__file__)) + '/services.ttl', 'w').write(generate_register(
        service_ids,
        datasets_services='services',
        mime='text/turtle'
    ))
   
    logger.info('Finished processing services')

    #
    #   Datasets, with pagination
    dataset_ids = get_ecat_ids(DATASET_CSW_URL, record_type='dataset')

    # make an HTML & a TTL file from those IDs
    open(os.path.dirname(os.path.realpath(__file__)) + '/datasets.html', 'w').write(generate_register(
        dataset_ids,
        datasets_services='datasets',
        mime='text/html',
        html_static_dir=STATIC_DIR
    ))

    open(os.path.dirname(os.path.realpath(__file__)) + '/datasets.ttl', 'w').write(generate_register(
        dataset_ids,
        datasets_services='datasets',
        mime='text/turtle'
    ))

    # staticreg
    sm_template = Environment(loader=FileSystemLoader(os.path.dirname(os.path.realpath(__file__)) + '/templates')) \
        .from_string(
        open(os.path.dirname(os.path.realpath(__file__)) + '/templates/datasets-metatag.html', 'r').read()
    )

    generated_datetime_str = datetime.now().strftime('%d %b %Y, %I:%M %p')
    open(os.path.dirname(os.path.realpath(__file__)) + '/datasets-metatag.html', 'w') \
        .write(sm_template.render(ids=dataset_ids, generated=generated_datetime_str))

    logger.info('Finished processing datasets')
    

# this only runs as a script
if __name__ == '__main__':
    # Setup logging handler if required
    if not logger.handlers:
        # Set handler for root root_logger to standard output
        console_handler = logging.StreamHandler(sys.stdout)
        #console_handler.setLevel(logging.INFO)
        console_handler.setLevel(logging.DEBUG)
        console_formatter = logging.Formatter('%(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
    if DEBUG:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
        
    main()
