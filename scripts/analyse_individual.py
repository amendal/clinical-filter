""" runs clinical filtering analysis on a single proband, just starting from the
proband ID. A helper script used for testing purposes.

Not recommended for use, as this is very scrappy code, and highly user-specific,
but it works if all the files are in the expected locations.
"""

import os
import sys
import argparse
import subprocess
import random
import glob

from clinicalfilter.ped import load_families

home_folder = os.path.expanduser('~')
app_folder = os.path.join(home_folder, "apps", "clinical-filter")

filter_code = os.path.join(app_folder, "bin", "clinical_filter.py")

datafreeze = "/nfs/ddd0/Data/datafreeze/ddd_data_releases/2015-04-13"
known_genes = "/lustre/scratch113/projects/ddd/resources/ddd_data_releases/2015-04-13/DDG2P/dd_genes_for_clinical_filter"
ped_file = os.path.join(datafreeze, "family_relationships.txt")
alternate_ids = os.path.join(datafreeze, "person_sanger_decipher.txt")
syndrome_regions_filename = "/lustre/scratch113/projects/ddd/resources/decipher_syndrome_list_20140428.txt"
LAST_BASE_PATH = "/lustre/scratch113/projects/ddd/users/jm33/last_base_sites_G.json"

def get_options():
    """ gets the options from the command line
    """
    
    parser = argparse.ArgumentParser(description="Submit analysis job for single individual")
    parser.add_argument('-i', '--individual', required=True, help='ID of proband to be analysed')
    parser.add_argument('--ped', help='pedigree file to use')
    parser.add_argument('--log', dest='loglevel', default="debug",
        help='level of logging to use, choose from: debug, info, warning, error or critical')
    parser.add_argument('--all-genes', default=False, action="store_true",
        help='Option to assess variants in all genes. If unused, restricts variants to DDG2P genes.')
    parser.add_argument('--debug-chrom', help='chromosome of variant to debug.')
    parser.add_argument('--debug-pos', help='position of variant to debug.')
    parser.add_argument('--without-parents', default=False, action="store_true",
        help='whether to remove the parents for a proband only-analysis.')
    parser.add_argument("--ignore-lof-tweak", default=False,
        action="store_true", help="whether to use the last base of exon rule.")
    
    args = parser.parse_args()
    
    return args

def load_ped(ped_path, proband_id, exclude_parents):
    """ loads the pedigree details for a prband
    
    Args:
        ped_path: path to pedigree file for cohort
        proband_id: individual Id for proband of interest
        exclude_parents: whether to exclude the parents of the proband
    """
    
    families = load_families(ped_path)
    families = [ family for family in families for person in family \
        if person is not None and person.get_id() == proband_id ]
    
    assert len(families) == 1
    family = families[0]
    
    lines = []
    for person in family:
        if person is None:
            continue
        
        line = '{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format(person.family_id,
            person.get_id(), person.dad_id, person.mom_id,
            person.get_gender(), person.get_affected_status(),
            person.get_path())
        lines.append(line)
    
    return lines

def get_random_string():
    """ make a random string, which we can use for bsub job IDs, so that
    different jobs do not have the same job IDs.
    
    Returns:
        random 8 character string
    """
    
    def is_number(string):
        try:
            number = float(string)
            return True
        except ValueError:
            return False
    
    # don't allow the random strings to be equivalent to a number, since
    # the LSF cluster interprets those differently from letter-containing
    # strings
    job_id = None
    while job_id is None or is_number(job_id):
        job_id = "{0:x}".format(random.getrandbits(32))
        job_id = job_id.strip()
    
    return job_id

def clean_folder(string):
    ''' clean the folder of old job array files'''
    
    for path in glob.glob(string + "*"):
        os.remove(path)

def main():
    """ analyse a single proband using bjobs
    """
    
    args = get_options()
    logging_option = ["--log", args.loglevel]
    
    ped = load_ped(args.ped, args.individual, args.without_parents)
    
    # remove the temp files from the previous run
    tmp_name = "tmp_run."
    clean_folder(tmp_name)
    
    # write the temp ped file for the family to a file, but make sure it doesn't overwrite anything
    path = tmp_name + get_random_string() + ".ped"
    with open(path, 'w') as handle:
        handle.writelines(ped)
    
    # now set up the command for analysing the given pedigree file
    bjobs_preamble = ["bsub", "-q", "normal", "-o", path + ".bjob_output.txt"]
    filter_command = ["python3", filter_code, \
        "--ped", path, \
        "--alternate-ids", alternate_ids, \
        "--output", path + ".output.txt", \
        "--export-vcf", os.getcwd(), \
        "--syndrome-regions", syndrome_regions_filename] + logging_option
    
    if not args.ignore_lof_tweak:
        filter_command += ["--lof-sites", LAST_BASE_PATH]
    
    if not args.all_genes:
        filter_command += ["--known-genes", known_genes]
    
    if args.debug_chrom is not None:
        filter_command += ["--debug-chrom", args.debug_chrom, "--debug-pos", args.debug_pos]
        
    full_command = " ".join(bjobs_preamble + filter_command)
    
    subprocess.call(bjobs_preamble + filter_command)

if __name__ == "__main__":
    main()
