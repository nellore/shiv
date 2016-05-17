#!/usr/bin/env python2.7
import sys
import os
import shutil
import subprocess

RUN_COL=0
PROJ_COL=1

#default locations/settings for aspera
aspera = "%s/.aspera/connect/bin/ascp" % (os.environ['HOME'])
akey = "-i %s/.aspera/connect/etc/asperaweb_id_dsa.openssh" % (os.environ['HOME'])
aparams = '-k 1 -T -l500m'
prefix = 'anonftp@ftp.ncbi.nlm.nih.gov:/sra/sra-instant/reads/ByRun/sra/'

#assume fastqdump is in path
fastqdump = 'fastq-dump'

#assume rclone is in path
rclone = '/data/rclone-v1.29-linux-amd64/rclone'
MAX_UPLOAD_FILE_SIZE = '49G'

#track projects already created on remote end
projs_seen = set()

def run_command(cmd):
  try:
    print("running %s" % (cmd))
    subprocess.check_output(cmd,shell=True)
  except subprocess.CalledProcessError, e:
    sys.stderr.write("%s raised errorcode %s with output %s\n" % (e.cmd,e.returncode,e.output))

def download_accession(run,dir_,just_upload):
  outdir = "%s/%s" % (dir_,run)
  if not os.path.isdir(outdir):
    os.mkdir(outdir)
  acmd = "%s %s %s %s/%s/%s/%s/%s.sra %s/" % (aspera,akey,aparams,prefix,run[:3],run[:6],run,run,outdir)
  if not just_upload:
    run_command(acmd)
  return outdir

def convert_accession(run,tmp_dir,proj_dir):
  run_dir = "%s/%s" % (proj_dir,run)
  if not os.path.isdir(run_dir):
    os.mkdir(run_dir)
  fcmd = "%s --split-files --gzip -O %s %s/%s/%s.sra" % (fastqdump,run_dir,tmp_dir,run,run)
  run_command(fcmd)

def upload_accession(remote_prefix,run,proj,outdir,logdir,acd_remote):
  #call rclone to copy outdir/run/ to remote:remote_prefix/proj/run
  remote_path = "%s/%s" % (remote_prefix,proj)
  if len(remote_prefix) == 0:
    remote_path = proj
  rcmd = "%s --log-file %s --max-size %s --transfers 1 copy %s %s:%s/" % (rclone,"%s/%s.log" % (logdir,run),MAX_UPLOAD_FILE_SIZE,outdir,acd_remote,remote_path)
  run_command(rcmd)

def remote_mkdir(remote_prefix,dir_to_create,logdir,acd_remote):
  remote_path = "%s/%s" % (remote_prefix,dir_to_create)
  if len(remote_prefix) == 0:
    remote_path = dir_to_create
  rcmd = "%s --log-file %s mkdir %s:%s" % (rclone,"%s/%s.log" % (logdir,dir_to_create),acd_remote,remote_path)
  run_command(rcmd)

def process_accessions(args):
    with open(args.accessions,"r") as fin:
      for line in fin:
        fields = line.rstrip().split(",")
        run = fields[RUN_COL]
        proj = fields[PROJ_COL]
        toutdir = "%s/%s" % (args.temp_dir,proj)
        if not os.path.isdir(toutdir):
          os.mkdir(toutdir)
        run_dir = download_accession(run,toutdir,args.just_upload)
        outdir = "%s/%s" % (args.out_dir,proj)
        if not os.path.isdir(outdir):
          os.mkdir(outdir)
        if not args.just_upload:
          convert_accession(run,toutdir,outdir)
        #toutdir = "%s/%s/%s" % (args.out_dir,proj,run)
        if proj not in projs_seen:
          remote_mkdir(args.remote_path_prefix,proj,args.log_dir,args.amazon_remote)
          projs_seen.add(proj)
        upload_accession(args.remote_path_prefix,run,proj,outdir,args.log_dir,args.amazon_remote)
        os.system("rm -rf %s/%s*" % (outdir,run))  
        os.system("rm -rf %s/%s*" % (toutdir,run))  

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
    parser.add_argument('-l', '--log-dir', type=str, default='./',
            help='directory to download to'
        )
    parser.add_argument('-r', '--amazon-remote', type=str, default='remote',
            help='Amazon Cloud Drive remote name'
        )
    parser.add_argument('-p', '--remote-path-prefix', type=str, default='',
            help='Amazon Cloud Drive remote path prefix'
        )
    parser.add_argument('-u', '--just-upload', action='store_true', default=False,
            help='If files already present, just upload them'
        )
    args = parser.parse_args()

    if not os.path.isdir(args.temp_dir):
      os.mkdir(args.temp_dir)
    
    if not os.path.isdir(args.out_dir):
      os.mkdir(args.out_dir)
    
    if not os.path.isdir(args.log_dir):
      os.mkdir(args.out_dir)

    process_accessions(args)

if __name__ == '__main__':
  main()


