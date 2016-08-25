'''
Copyright (c) 2016 Genome Research Ltd.

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''

import tempfile
import shutil

import unittest
from clinicalfilter.load_files import get_header_positions, \
    parse_gene_line,  open_known_genes, create_person_ID_mapper, \
    open_cnv_regions

class TestLoadFilesPy(unittest.TestCase):
    ''' test the file loading functions
    '''
    
    @classmethod
    def setUpClass(cls):
        cls.tempdir = tempfile.mkdtemp()
    
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tempdir)
    
    def setUp(self):
        ''' make sure we are only going to be working on temporary files
        '''
        
        self.temp = tempfile.NamedTemporaryFile(dir=self.tempdir, delete=False)
    
    def test_get_header_positions(self):
        ''' check that get_header_positions() works correctly
        '''
        
        self.temp.write('chrom\tstart\tstop\thgnc\n'.encode('utf8'))
        self.temp.flush()
        
        with open(self.temp.name) as handle:
            self.assertEqual(get_header_positions(handle, ['chrom', 'stop',
                'hgnc']), {'chrom': 0, 'stop': 2, 'hgnc': 3})
        
        # raise an error if we try to get a column name that does not appear in
        # the header
        with open(self.temp.name) as handle:
            with self.assertRaises(ValueError):
                get_header_positions(handle, ['chrom', 'stop', 'missing'])
    
    def test_parse_gene_line(self):
        ''' check that parse_gene_line() works correctly
        '''
        
        header = {'gene': 0, 'chr': 1, 'start': 2, 'stop': 3, 'type': 4,
            'mode': 5, 'mech': 6}
        
        line = ['TEST', 'chr1', '1000', '2000', 'Confirmed DD Gene',
            'Biallelic', 'Loss-of-function']
        
        self.assertEqual(parse_gene_line(line, header), ('TEST', {
            'chrom': 'chr1', 'start': 1000, 'end': 2000,
            'status': set(['Confirmed DD Gene']),
            'inh': {'Biallelic': set(['Loss-of-function'])}}))
    
    def test_parse_gene_line_both_mechanism(self):
        ''' check that parse_gene_line() works correctly for 'Both' mechanism.
        '''
        
        header = {'gene': 0, 'chr': 1, 'start': 2, 'stop': 3, 'type': 4,
            'mode': 5, 'mech': 6}
        line = ['TEST', 'chr1', '1000', '2000', 'Confirmed DD Gene',
            'Both', 'Loss-of-function']
        
        self.assertEqual(parse_gene_line(line, header), ('TEST', {
            'chrom': 'chr1', 'start': 1000, 'end': 2000,
            'status': set(['Confirmed DD Gene']),
            'inh': {'Biallelic': set(['Loss-of-function']),
                'Monoallelic': set(['Loss-of-function']),
                'Both': set(['Loss-of-function'])}}))
    
    def test_open_known_genes(self):
        ''' test that open_known_genes() works correctly
        '''
        
        header = ['gene', 'chr', 'start', 'stop', 'type', 'mode', 'mech']
        line = ['TEST', '1', '1000', '2000', 'Confirmed DD Gene',
            'Monoallelic', 'Loss-of-function']
        
        self.temp.write(('\t'.join(header) + '\n').encode('utf8'))
        self.temp.write(('\t'.join(line) + '\n').encode('utf8'))
        self.temp.flush()
        
        self.assertEqual(open_known_genes(self.temp.name),
            {'TEST': {'chrom': '1', 'start': 1000, 'end': 2000,
                'status': set(['Confirmed DD Gene']),
                'inh': {'Monoallelic': set(['Loss-of-function'])}}
            })
    
    def test_open_known_genes_multimodes(self):
        ''' test that open_known_genes() works correctly for genes with >1 modes
        '''
        
        header = ['gene', 'chr', 'start', 'stop', 'type', 'mode', 'mech']
        line1 = ['TEST', '1', '1000', '2000', 'Confirmed DD Gene',
            'Monoallelic', 'Loss-of-function']
        line2 = ['TEST', '1', '1000', '2000', 'Confirmed DD Gene',
            'Biallelic', 'Loss-of-function']
        
        self.temp.write(('\t'.join(header) + '\n').encode('utf8'))
        self.temp.write(('\t'.join(line1) + '\n').encode('utf8'))
        self.temp.write(('\t'.join(line2) + '\n').encode('utf8'))
        self.temp.flush()
        
        self.assertEqual(open_known_genes(self.temp.name),
            {'TEST': {'chrom': '1', 'start': 1000, 'end': 2000,
                'status': set(['Confirmed DD Gene']),
                'inh': {'Monoallelic': set(['Loss-of-function']),
                     'Biallelic': set(['Loss-of-function'])}}
            })
    
    def test_open_known_genes_multimechs(self):
        ''' test that open_known_genes() works correctly for genes with >1 mechs
        '''
        
        header = ['gene', 'chr', 'start', 'stop', 'type', 'mode', 'mech']
        line1 = ['TEST', '1', '1000', '2000', 'Confirmed DD Gene',
            'Monoallelic', 'Loss-of-function']
        line2 = ['TEST', '1', '1000', '2000', 'Confirmed DD Gene',
            'Monoallelic', 'Activating']
        
        self.temp.write(('\t'.join(header) + '\n').encode('utf8'))
        self.temp.write(('\t'.join(line1) + '\n').encode('utf8'))
        self.temp.write(('\t'.join(line2) + '\n').encode('utf8'))
        self.temp.flush()
        
        self.assertEqual(open_known_genes(self.temp.name),
            {'TEST': {'chrom': '1', 'start': 1000, 'end': 2000,
                'status': set(['Confirmed DD Gene']),
                'inh': {'Monoallelic': set(['Loss-of-function', 'Activating'])}}
            })
    
    def test_open_known_genes_multigenes(self):
        ''' test that open_known_genes() works correctly for multiple genes
        '''
        
        header = ['gene', 'chr', 'start', 'stop', 'type', 'mode', 'mech']
        line1 = ['TEST', '1', '1000', '2000', 'Confirmed DD Gene',
            'Monoallelic', 'Loss-of-function']
        line2 = ['TEST2', '1', '3000', '4000', 'Confirmed DD Gene',
            'Monoallelic', 'Loss-of-function']
        
        self.temp.write(('\t'.join(header) + '\n').encode('utf8'))
        self.temp.write(('\t'.join(line1) + '\n').encode('utf8'))
        self.temp.write(('\t'.join(line2) + '\n').encode('utf8'))
        self.temp.flush()
        
        self.assertEqual(open_known_genes(self.temp.name),
            {'TEST': {'chrom': '1', 'start': 1000, 'end': 2000,
                'status': set(['Confirmed DD Gene']),
                'inh': {'Monoallelic': set(['Loss-of-function'])}},
            'TEST2': {'chrom': '1', 'start': 3000, 'end': 4000,
                'status': set(['Confirmed DD Gene']),
                'inh': {'Monoallelic': set(['Loss-of-function'])}}
            })
    
    def test_open_known_genes_wrong_status(self):
        ''' test that open_known_genes() filters out genes without a good status
        '''
        
        header = ['gene', 'chr', 'start', 'stop', 'type', 'mode', 'mech']
        line1 = ['TEST', '1', '1000', '2000', 'Possible DD Gene',
            'Monoallelic', 'Loss-of-function']
        line2 = ['TEST2', '1', '3000', '4000', 'Confirmed DD Gene',
            'Monoallelic', 'Loss-of-function']
        
        self.temp.write(('\t'.join(header) + '\n').encode('utf8'))
        self.temp.write(('\t'.join(line1) + '\n').encode('utf8'))
        self.temp.write(('\t'.join(line2) + '\n').encode('utf8'))
        self.temp.flush()
        
        self.assertEqual(open_known_genes(self.temp.name),
            {'TEST2': {'chrom': '1', 'start': 3000, 'end': 4000,
                'status': set(['Confirmed DD Gene']),
                'inh': {'Monoallelic': set(['Loss-of-function'])}}
            })
    
    def test_open_known_genes_missing_lines(self):
        ''' test that open_known_genes() works correctly when we can't find any genes
        '''
        
        header = ['gene', 'chr', 'start', 'stop', 'type', 'mode', 'mech']
        
        self.temp.write(('\t'.join(header) + '\n').encode('utf8'))
        self.temp.flush()
        
        # if we have checked the file, and there aren't any genes in it, this
        # raises an error, since the most likely explanation is that something
        # has gone wrong with the data file, and likely the line-endings
        with self.assertRaises(ValueError):
            open_known_genes(self.temp.name)
    
    def test_create_person_ID_mapper(self):
        ''' test that create_person_ID_mapper() works correctly
        '''
        
        lines = ['sample_id\talt_id\n',
            'sample_01\tdecipher55\n',
            'sample_02\tdecipher77\n',]
        
        lines = [ x.encode('utf8') for x in lines ]
        self.temp.writelines(lines)
        self.temp.flush()
        
        self.assertEqual(create_person_ID_mapper(self.temp.name), {
            'sample_id': 'alt_id', 'sample_01': 'decipher55',
            'sample_02': 'decipher77'})
    
    def test_create_person_ID_mapper_dups_and_parents(self):
        ''' test that create_person_ID_mapper() works with parents lines
        '''
        
        # make sure we can handle duplicate lines, and lines for parental data
        lines = ['sample_id\talt_id\n',
            'sample_01\tdecipher55\n',
            'sample_02\tdecipher77\n',
            'sample_02\tdecipher77\n',
            'sample_03\tdecipher55:pat\n',
            'sample_04\tdecipher77:mat\n']
        
        lines = [ x.encode('utf8') for x in lines ]
        self.temp.writelines(lines)
        self.temp.flush()
        
        self.assertEqual(create_person_ID_mapper(self.temp.name), {
            'sample_id': 'alt_id', 'sample_01': 'decipher55',
            'sample_02': 'decipher77'})
    
    def test_open_cnv_regions(self):
        ''' test that open_cnv_regions() works correctly
        '''
        
        lines = ['id_syndrome_feature\tid_syndrome\tcopy_number\tchr_start\tchr_end\tchr\n',
            '20\t1\t1\t1569197\t2110236\t4\tNA\t2650330\t149066\t1t\n']
        lines = [ x.encode('utf8') for x in lines ]
        
        self.temp.writelines(lines)
        self.temp.flush()
        
        self.assertEqual(open_cnv_regions(self.temp.name),
            {('4', '1569197', '2110236'): '1'})
        
    