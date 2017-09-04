import make_registers
from lxml import etree


def extract_ecat_ids_sax(xml_file, ids_file):
    ids = make_registers.extract_ecat_ids(xml_file)
    print(len(ids))
    open(ids_file, 'w').write('\n'.join((str(id) for id in ids)))


def extract_ecat_ids_xpath(xml_file, ids_file):
    namespaces = {
        'mdb': 'http://standards.iso.org/iso/19115/-3/mdb/1.0',
        'cat': 'http://standards.iso.org/iso/19115/-3/cat/1.0',
        'cit': 'http://standards.iso.org/iso/19115/-3/cit/1.0',
        'gcx': 'http://standards.iso.org/iso/19115/-3/gcx/1.0',
        'gex': 'http://standards.iso.org/iso/19115/-3/gex/1.0',
        'lan': 'http://standards.iso.org/iso/19115/-3/lan/1.0',
        'srv': 'http://standards.iso.org/iso/19115/-3/srv/2.0',
        'mas': 'http://standards.iso.org/iso/19115/-3/mas/1.0',
        'mcc': 'http://standards.iso.org/iso/19115/-3/mcc/1.0',
        'mco': 'http://standards.iso.org/iso/19115/-3/mco/1.0',
        'mda': 'http://standards.iso.org/iso/19115/-3/mda/1.0',
        'mds': 'http://standards.iso.org/iso/19115/-3/mds/1.0',
        'mdt': 'http://standards.iso.org/iso/19115/-3/mdt/1.0',
        'mex': 'http://standards.iso.org/iso/19115/-3/mex/1.0',
        'mmi': 'http://standards.iso.org/iso/19115/-3/mmi/1.0',
        'mpc': 'http://standards.iso.org/iso/19115/-3/mpc/1.0',
        'mrc': 'http://standards.iso.org/iso/19115/-3/mrc/1.0',
        'mrd': 'http://standards.iso.org/iso/19115/-3/mrd/1.0',
        'mri': 'http://standards.iso.org/iso/19115/-3/mri/1.0',
        'mrl': 'http://standards.iso.org/iso/19115/-3/mrl/1.0',
        'mrs': 'http://standards.iso.org/iso/19115/-3/mrs/1.0',
        'msr': 'http://standards.iso.org/iso/19115/-3/msr/1.0',
        'mdq': 'http://standards.iso.org/iso/19157/-2/mdq/1.0',
        'mac': 'http://standards.iso.org/iso/19115/-3/mac/1.0',
        'gco': 'http://standards.iso.org/iso/19115/-3/gco/1.0',
        'gml': 'http://www.opengis.net/gml/3.2',
        'xlink': 'http://www.w3.org/1999/xlink',
        'geonet': 'http://www.fao.org/geonetwork'
    }
    r = etree.parse(xml_file)
    '''
            <mri:MD_DataIdentification>
          <mri:citation>
            <cit:CI_Citation>
              <cit:title>
                <gco:CharacterString>Burra 1:250 000 topographic map</gco:CharacterString>
              </cit:title>
              <cit:identifier>
                <mcc:MD_Identifier>
                  <mcc:code>
                    <gco:CharacterString>
    '''
    # candidates = r.xpath('//mri:MD_DataIdentification/mri:citation/cit:CI_Citation/cit:identifier/mcc:MD_Identifier/mcc:code/gco:CharacterString/text()|'
    #                      '//srv:SV_ServiceIdentification/mri:citation/cit:CI_Citation/cit:identifier/mcc:MD_Identifier/mcc:code/gco:CharacterString/text()|'
    #                      '',
    #                      namespaces=namespaces
    #                      )

    ids = r.xpath('//mdb:MD_Metadata/mdb:alternativeMetadataReference/cit:CI_Citation/cit:identifier/mcc:MD_Identifier/mcc:code/gco:CharacterString/text()',
                         namespaces=namespaces
                         )
    open(ids_file, 'w').write('\n'.join([str(x) for x in sorted(ids)]))
    print(len(ids))


def count_records(xml_file):
    namespaces = {
        'mdb': 'http://standards.iso.org/iso/19115/-3/mdb/1.0',
        'cat': 'http://standards.iso.org/iso/19115/-3/cat/1.0',
        'cit': 'http://standards.iso.org/iso/19115/-3/cit/1.0',
        'gcx': 'http://standards.iso.org/iso/19115/-3/gcx/1.0',
        'gex': 'http://standards.iso.org/iso/19115/-3/gex/1.0',
        'lan': 'http://standards.iso.org/iso/19115/-3/lan/1.0',
        'srv': 'http://standards.iso.org/iso/19115/-3/srv/2.0',
        'mas': 'http://standards.iso.org/iso/19115/-3/mas/1.0',
        'mcc': 'http://standards.iso.org/iso/19115/-3/mcc/1.0',
        'mco': 'http://standards.iso.org/iso/19115/-3/mco/1.0',
        'mda': 'http://standards.iso.org/iso/19115/-3/mda/1.0',
        'mds': 'http://standards.iso.org/iso/19115/-3/mds/1.0',
        'mdt': 'http://standards.iso.org/iso/19115/-3/mdt/1.0',
        'mex': 'http://standards.iso.org/iso/19115/-3/mex/1.0',
        'mmi': 'http://standards.iso.org/iso/19115/-3/mmi/1.0',
        'mpc': 'http://standards.iso.org/iso/19115/-3/mpc/1.0',
        'mrc': 'http://standards.iso.org/iso/19115/-3/mrc/1.0',
        'mrd': 'http://standards.iso.org/iso/19115/-3/mrd/1.0',
        'mri': 'http://standards.iso.org/iso/19115/-3/mri/1.0',
        'mrl': 'http://standards.iso.org/iso/19115/-3/mrl/1.0',
        'mrs': 'http://standards.iso.org/iso/19115/-3/mrs/1.0',
        'msr': 'http://standards.iso.org/iso/19115/-3/msr/1.0',
        'mdq': 'http://standards.iso.org/iso/19157/-2/mdq/1.0',
        'mac': 'http://standards.iso.org/iso/19115/-3/mac/1.0',
        'gco': 'http://standards.iso.org/iso/19115/-3/gco/1.0',
        'gml': 'http://www.opengis.net/gml/3.2',
        'xlink': 'http://www.w3.org/1999/xlink',
        'geonet': 'http://www.fao.org/geonetwork'
    }
    r = etree.parse(xml_file)
    records = r.xpath('//mdb:MD_Metadata/mdb:identificationInfo',
                         namespaces=namespaces
                         )
    print(etree.tostring(records[0], pretty_print=True).decode('utf-8'))

if __name__ == '__main__':
    pass
