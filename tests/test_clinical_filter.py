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

import unittest
import tempfile
import shutil

from clinicalfilter.filter import Filter
from clinicalfilter.ped import Family, Person
from clinicalfilter.variant.snv import SNV
from clinicalfilter.trio_genotypes import TrioGenotypes

from tests.utils import create_variant
from tests.utils import make_vcf_header, make_vcf_line


class TestFilterPy(unittest.TestCase):
    """ test the Filter class
    """
    
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.mkdtemp()
    
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.temp_dir)
    
    def setUp(self):
        """ create a default Filter object to test
        """
        
        count = 1
        regions = None
        known_genes, genes_date = None, None
        output_path, export_vcf = None, None
        debug_chrom, debug_pos = None, None
        pp_filter = 0.9
        lof_sites = None
        population_tags = ["AFR_AF", "AMR_AF", "ASN_AF", "DDD_AF", "EAS_AF",
            "ESP_AF", "EUR_AF", "MAX_AF", "SAS_AF", "UK10K_cohort_AF"]
        sum_x_lr2 = None#
        
        self.finder = Filter(population_tags, count, known_genes, genes_date,
            regions, lof_sites, pp_filter, sum_x_lr2, output_path, export_vcf, debug_chrom,
            debug_pos)
    
    def test_analyse_trio(self):
        ''' test that analyse_trio() works correctly
        '''
        
        # construct the VCFs for the trio members
        paths = {}
        for member in ['child', 'mom', 'dad']:
            vcf = make_vcf_header()
            
            geno, pp_dnm = '0/0', ''
            if member == 'child':
                geno, pp_dnm = '0/1', ';DENOVO-SNP;PP_DNM=1'
            
            vcf.append(make_vcf_line(genotype=geno, extra='HGNC=ARID1B' + pp_dnm))
            
            # write the VCF data to a file
            handle = tempfile.NamedTemporaryFile(dir=self.temp_dir, delete=False,
                suffix='.vcf')
            for x in vcf:
                handle.write(x.encode('utf8'))
            handle.flush()
            
            paths[member] = handle.name
        
        # create a Family object, so we can load the data from the trio's VCFs
        fam_id = 'fam01'
        child = Person(fam_id, 'child', 'dad', 'mom', 'female', '2', paths['child'])
        mom = Person(fam_id, 'mom', '0', '0', 'female', '1', paths['mom'])
        dad = Person(fam_id, 'dad', '0', '0', 'male', '1', paths['dad'])
        family = Family(fam_id, [child], mom, dad)
        
        self.assertEqual(self.finder.analyse_trio(family),
            [(TrioGenotypes(chrom="1", pos=1,
                child=SNV(chrom="1", position=1, id=".", ref="G", alts="T",
                    qual='1000', filter="PASS",
                    info="CQ=missense_variant;DENOVO-SNP;HGNC=ARID1B;PP_DNM=1",
                    format="DP:GT", sample="50:0/1", gender="female", mnv_code=None),
                mother=SNV(chrom="1", position=1, id=".", ref="G", alts="T",
                    qual='1000', filter="PASS", info="CQ=missense_variant;HGNC=ARID1B",
                    format="DP:GT", sample="50:0/0", gender="female", mnv_code=None),
                father=SNV(chrom="1", position=1, id=".", ref="G", alts="T",
                    qual='1000', filter="PASS", info="CQ=missense_variant;HGNC=ARID1B",
                    format="DP:GT", sample="50:0/0", gender="male", mnv_code=None)),
            ['single_variant'], ['Monoallelic', 'Mosaic'], ['ARID1B'])])
    
    def test_create_gene_dict(self):
        """ test that create_gene_dict works correctly
        """
        
        # create variants that share genes, or not
        snv1 = create_variant("F", "missense_variant|missense_variant", "TEST1|TEST2")
        snv2 = create_variant("F", "missense_variant", "TEST1")
        snv3 = create_variant("F", "missense_variant", "OTHER1")
        
        # the variants that share a gene should be grouped in lists indexed by
        # the gene key
        self.assertEqual(self.finder.create_gene_dict([snv1, snv2, snv3]),
            {"TEST1": [snv1, snv2], "TEST2": [snv1], "OTHER1": [snv3]})
    
    def test_find_variants(self):
        """ test that find_variants() works correctly
        """
        
        # define the trio, so that we can know whether the parents are affected.
        # The child also needs to be included and set, so that we can get the
        # child ID for logging purposes.
        family = Family("famID")
        family.add_child("child_id", 'dad_id', 'mom_id', 'f', '2', "/vcf/path")
        family.add_father("dad_id", '0', '0', 'm', '1', "/vcf/path")
        family.add_mother("mom_id", '0', '0', 'f', '1', "/vcf/path")
        family.set_child()
        
        # create variants that cover various scenarios
        snv1 = create_variant("F", "missense_variant|missense_variant", "TEST1|TEST2")
        snv2 = create_variant("F", "missense_variant|synonymous_variant", "OTHER1|OTHER2")
        snv3 = create_variant("F", "missense_variant", "")
        snv4 = create_variant("F", "missense_variant", "TESTX", chrom="X")
        
        self.finder.known_genes = {"TEST1": {"inh": ["Monoallelic"]},
            "OTHER1": {"inh": ["Monoallelic"]},
            "OTHER2": {"inh": ["Monoallelic"]},
            "TESTX": {"inh": ["X-linked dominant"]}}
        
        # check the simplest case, a variant in a known gene
        self.assertEqual(self.finder.find_variants([snv1], "TEST1", family),
            [(snv1, ["single_variant"], ["Monoallelic"], ["TEST1"])])
        
        # check that a gene not in a known gene does not pass
        self.assertEqual(self.finder.find_variants([snv1], "TEST2", family), [])
        
        # check a variant where the gene is known, but the consequence for that
        # gene is not functional, does not pass
        self.assertEqual(self.finder.find_variants([snv2], "OTHER2", family), [])
        
        # check that intergenic variants (which lack HGNC symbols) do not pass
        self.assertEqual(self.finder.find_variants([snv3], None, family), [])
        
        # check that a variant on chrX passes through the allosomal instance
        self.assertEqual(self.finder.find_variants([snv4], "TESTX", family),
            [(snv4, ["single_variant"], ["X-linked dominant"], ["TESTX"])])
        
        # remove the known genes, so that the variants in unknown genes pass
        self.finder.known_genes = None
        self.assertEqual(sorted(self.finder.find_variants([snv1], "TEST2", family)),
            [(snv1, ["single_variant"], ["Monoallelic"], ["TEST2"]),
            (snv1, ["single_variant"], ["Mosaic"], ["TEST2"])])
        
        # but variants without gene symbols still are excluded
        self.assertEqual(self.finder.find_variants([snv3], None, family), [])
    
    def test_exclude_duplicates(self):
        """ test that exclude duplicates works correctly
        """
        
        # create a variant that is within two genes
        snv1 = create_variant("F", "missense_variant|missense_variant", "TEST1|TEST2")
        
        # two variants that lie in different genes on different chromosomes
        # should not be merged
        snv2 = create_variant("F", "missense_variant", "OTHER1", chrom="2")
        variants = [(snv1, ["single_variant"], ["Monoallelic"], ["TEST1"]),
            ((snv2, ["single_variant"], ["Monoallelic"], ["OTHER1"]))]
        self.assertEqual(sorted(self.finder.exclude_duplicates(variants)), sorted(variants))
        
        # create a list of variant tuples that passed filtering for two
        # different gene symbols
        variants = [(snv1, ["single_variant"], ["Monoallelic"], ["TEST1"]),
            ((snv1, ["compound_het"], ["Biallelic"], ["TEST1"])),
            ((snv1, ["compound_het"], ["Biallelic"], ["TEST1"]))]
        self.assertEqual(self.finder.exclude_duplicates(variants),
            [(snv1, ["compound_het", "single_variant"], ["Biallelic", "Monoallelic"], ["TEST1"])])
        
        # create a list of variant tuples that passed filtering for two
        # different gene symbols
        variants = [(snv1, ["single_variant"], ["Monoallelic"], ["TEST1"]),
            ((snv1, ["single_variant"], ["Monoallelic"], ["TEST2"]))]
        
        # the same variant passing for two gene symbols should be collapsed
        # into a single entry, where the entry contains a list ofall the gene
        # symbols
        self.assertEqual(self.finder.exclude_duplicates(variants),
            [(snv1, ["single_variant"], ["Monoallelic"], ["TEST1", "TEST2"])])
        
