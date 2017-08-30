import os
import math
import requests
import xml.sax as x
from xml.etree import cElementTree
from jinja2 import Environment, FileSystemLoader
from datetime import datetime


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
                      stream=True)
    return r.raw


def make_csw_request_xml(start_position, max_records):
    xml_template_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'templates',
        'csw_request_records.xml')
    xml = open(xml_template_path, 'r').read()
    xml = xml.replace('{{ start_position }}', str(start_position))
    xml = xml.replace('{{ max_records }}', str(max_records))
    return xml


def get_total_no_of_records(csw_endpoint):
    xml_template_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'templates',
        'csw_request_count.xml')
    xml = open(xml_template_path, 'r').read().encode('utf-8')
    print(xml)

    r = requests.post(csw_endpoint,
                      data=xml,
                      headers={'Content-Type': 'application/xml'})

    # extract the number of hits
    return r.content
    #return int(re.findall('numberOfRecordsMatched="(\d+)"', r.content.decode('utf-8'))[0])


class IdHandler(x.ContentHandler):
    # see http://python.zirael.org/e-sax2.html
    def __init__(self):
        x.ContentHandler.__init__(self)
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
        if localname == 'identificationInfo':
            self.one = True
        if (self.one and localname == 'SV_ServiceIdentification') or self.one and localname == 'MD_DataIdentification':
            self.two = True
        if self.two and localname == 'citation':
            self.three = True
        if self.three and localname == 'CI_Citation':
            # if the parent tag of the CI_citation != 'citation' (e.g. 'authority' for EPSG code), restart seq checker
            if self.parent[-1] == 'citation':
                self.four = True
            else:
                self.parent = []
                self.one = False
                self.two = False
                self.three = False
                self.four = False
                self.five = False
                self.six = False
                self.seven = False
        if self.four and localname == 'RS_Identifier':
            self.five = True
        if self.five and localname == 'code':
            self.six = True
        if self.six and localname == 'CharacterString':
            self.seven = True

        self.parent.append(localname)

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
    parser = x.make_parser()
    parser.setContentHandler(n)
    parser.setFeature(x.handler.feature_namespaces, True)
    parser.parse(open(csw_result_file, 'r'))

    return sorted(n.ids)


def extract_ecat_ids_stream(result_stream):
    n = IdHandler()
    parser = x.make_parser()
    parser.setContentHandler(n)
    parser.setFeature(x.handler.feature_namespaces, True)
    parser.parse(result_stream)

    return sorted(n.ids)


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


# this only runs as a script
if __name__ == '__main__':
    datasets_csw_endpoint = 'https://ecat.ga.gov.au/geonetwork/srv/eng/csw'
    datasets_xml = 'datasets.xml'
    datasets_uri_base = 'http://pid.geoscience.gov.au/dataset/'
    datasets_ids = 'datasets.txt1'
    datasets_uris = 'datasets.txt'
    services_csw_endpoint = 'https://ecat.ga.gov.au/geonetwork/srv/eng/csw-services'
    services_xml = 'services.xml'
    services_uri_base = 'http://pid.geoscience.gov.au/service/'
    services_uris = 'services.txt'
    static_dir = 'http://13.54.73.187/static'

    #
    #   Services
    #
    # get all the service IDs from eCat's Service's virtual CSW endpoint
    request_query = make_csw_request_xml(1, 1000)
    ids = extract_ecat_ids_stream(stream_csw_request(services_csw_endpoint, request_query))

    # make an HTML & a TTL file from those IDs
    open(os.path.dirname(os.path.realpath(__file__)) + '/services.html', 'w').write(generate_register(
        ids,
        datasets_services='services',
        mime='text/html',
        html_static_dir=static_dir
    ))

    open(os.path.dirname(os.path.realpath(__file__)) + '/services.ttl', 'w').write(generate_register(
        ids,
        datasets_services='services',
        mime='text/turtle'
    ))

    print('finished services')

    #
    #   Datasets, with pagination
    #
    # get all the service IDs from eCat's Datasets's virtual CSW endpoint
    # get the total number of records
    # num_records = get_total_no_of_records('http://ecat.ga.gov.au/geonetwork/srv/eng/csw')
    num_records = 30000
    page_size = 1000

    # calculate the total number of page calls
    no_pages = int(math.ceil(num_records / page_size))

    # paginate the response until no_page_calls reached, adding result of each page request to ids list
    ids = []
    page = 1
    while page <= no_pages:
        start_position = (page - 1) * page_size + 1
        paged_query = make_csw_request_xml(start_position, page_size)
        # request one page
        print('requesting page {} of {}'.format(page, no_pages))
        i = extract_ecat_ids_stream(stream_csw_request(datasets_csw_endpoint, paged_query))
        print('page ids: {}'.format(len(i)))
        ids.extend(i)

        page += 1

    print('total: {}'.format(len(ids)))

    # make an HTML & a TTL file from those IDs
    open(os.path.dirname(os.path.realpath(__file__)) + '/datasets.html', 'w').write(generate_register(
        ids,
        datasets_services='datasets',
        mime='text/html',
        html_static_dir=static_dir
    ))

    open(os.path.dirname(os.path.realpath(__file__)) + '/datasets.ttl', 'w').write(generate_register(
        ids,
        datasets_services='datasets',
        mime='text/turtle'
    ))

    # staticreg
    sm_template = Environment(loader=FileSystemLoader(os.path.dirname(os.path.realpath(__file__)) + '/templates')) \
        .from_string(
        open(os.path.dirname(os.path.realpath(__file__)) + '/templates/datasets-metatag.html', 'r').read()
    )

    generated_datetime_str = datetime.now().strftime('%d %b %Y, %-I:%M %p')
    open(os.path.dirname(os.path.realpath(__file__)) + '/datasets-metatag.html', 'w') \
        .write(sm_template.render(ids=ids, generated=generated_datetime_str))

    print('finished datasets')
