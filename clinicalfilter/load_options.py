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

import argparse

def get_options():
    """gets the options from the command line
    """
    
    parser = argparse.ArgumentParser(description="Filter VCFs for inherited"
        "variants in trios.")
    
    # the --ped and --child options are mutually exclusive
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--ped", help="Path to ped file containing cohort details for multiple trios.")
    group.add_argument("--child", help="Path to child's VCF file.")
    
    parser.add_argument("--mother", help="Path to mother's VCF file.")
    parser.add_argument("--father", help="Path to father's VCF file.")
    parser.add_argument("--gender", help="The child's gender (male or female).")
    parser.add_argument("--mom-aff", help="Mother's affected status (1=unaffected, or 2=affected).")
    parser.add_argument("--dad-aff", help="Father's affected status (1=unaffected, or 2=affected).")
    
    parser.add_argument("--syndrome-regions", dest="regions", help="Path to list of CNV regions known to occur in disorders.")
    parser.add_argument("--known-genes", help="Path to table of known disease causative genes.")
    parser.add_argument("--known-genes-date", dest="genes_date", help="Date that the list of known disease causative genes was last updated, used to track the version of known-genes used for analysis.")
    parser.add_argument("--alternate-ids", help="Path to table of alternate IDs, used to map individual IDs to their alternate study IDs.")
    parser.add_argument("-o", "--output", help="Path for analysis output in tabular format.")
    parser.add_argument("--export-vcf", help="Directory or file path for analysis output in VCF format.")
    parser.add_argument("--log", dest="loglevel", default="debug", help="Level of logging to use, choose from: debug, info, warning, error or critical.")
    parser.add_argument("--debug-chrom", help="chromosome of variant for which to debug the filtering behaviour.")
    parser.add_argument("--debug-pos", type=int, help="position of variant for which to debug the filtering behaviour.")
    parser.add_argument("--lof-sites", help="path to file of sites at the last base of exons that are potentially LoF sites.")
    
    # New argument added by PJ to allow DNM_PP filtering to be disabled.
    parser.add_argument("--pp-dnm-threshold", dest="pp_filter", type=float, default=0.9, help="Set PP_DNM threshold for filtering (defaults to >=0.9)")

    args = parser.parse_args()
    
    if args.child is not None and args.alternate_ids is not None:
        argparse.ArgumentParser.error("You can't specify alternate IDs when using --child")

    if args.pp_filter < 0.0 or args.pp_filter > 1:
        argparse.ArgumentParser.error("--pp-dnm-threshold must be between 0 and 1")
    
    return args
