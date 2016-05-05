#!/usr/bin/env python2.7
import sys
import os
import shutil
import subprocess

RUN_COL=0
PROJ_COL=1 #20

#default locations/settings for aspera
aspera = "%s/.aspera/connect/bin/ascp" % (os.environ['HOME'])
akey = "-i %s/.aspera/connect/etc/asperaweb_id_dsa.openssh" % (os.environ['HOME'])
aparams = '-k 1 -T -l500m'
prefix = 'anonftp@ftp.ncbi.nlm.nih.gov:/sra/sra-instant/reads/ByRun/sra/'

#assume fastqdump is in path
fastqdump = 'fastq-dump'

def run_command(cmd):
  try:
    print("running %s" % (cmd))
    subprocess.check_output(cmd,shell=True)
  except subprocess.CalledProcessError, e:
    sys.stderr.write("%s raised errorcode %s with output %s\n" % (e.cmd,e.returncode,e.output))

def download_accession(run,dir_):
  outdir = "%s/%s" % (dir_,run)
  if not os.path.isdir(outdir):
    os.mkdir(outdir)
  acmd = "%s %s %s %s/%s/%s/%s/%s.sra %s/" % (aspera,akey,aparams,prefix,run[:3],run[:6],run,run,outdir)
  #run_command(acmd)
  return outdir

def convert_accession(run,tmp_dir,proj_dir):
  run_dir = "%s/%s" % (proj_dir,run)
  if not os.path.isdir(run_dir):
    os.mkdir(run_dir)
  fcmd = "%s --split-files --gzip -O %s %s/%s/%s.sra" % (fastqdump,run_dir,tmp_dir,run,run)
  run_command(fcmd)

def process_accessions(accF,tdir_,dir_):
    with open(accF,"r") as fin:
      for line in fin:
        fields = line.rstrip().split(",")
        run = fields[RUN_COL]
        proj = fields[PROJ_COL]
        toutdir = "%s/%s" % (tdir_,proj)
        if not os.path.isdir(toutdir):
          os.mkdir(toutdir)
        #run_dir = download_accession(run,toutdir)
        outdir = "%s/%s" % (dir_,proj)
        if not os.path.isdir(outdir):
          os.mkdir(outdir)
        convert_accession(run,toutdir,outdir)
    #archive_path = archive_accession_files(args.accession,acc_dir)
    #upload_accession(args.accession,archive_path)

def main():
    import argparse
    # Print file's docstring if -h is invoked
    parser = argparse.ArgumentParser(description=__doc__, 
                formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('-a', '--accessions', type=str, required=True,
            help='accession list to download'
        )
    parser.add_argument('-d', '--out-dir', type=str, required=True,
            help='directory to convert and upload from'
        )
    parser.add_argument('-t', '--temp-dir', type=str, default='./',
            help='directory to download to'
        )
    args = parser.parse_args()

    if not os.path.isdir(args.temp_dir):
      os.mkdir(args.temp_dir)
    
    if not os.path.isdir(args.out_dir):
      os.mkdir(args.out_dir)
 
    process_accessions(args.accessions,args.temp_dir,args.out_dir) 
   

if __name__ == '__main__':
  main()


