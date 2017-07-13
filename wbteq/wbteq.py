# coding=utf-8
#!/usr/bin/env python

import argparse
import sys
import os
from datetime import datetime
import os.path
import re
from collections import namedtuple
import logging
from subprocess import call

from . import __version__


Job = namedtuple('Job',['job_id','job_name','job_email'])
Step = namedtuple('Step',['job_id','step_id','filename','seq_num'])
Param = namedtuple('Param',['step_id','param_name','param_value'])

logger = logging.getLogger('WBTEQ')
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)


def _check_folder(folder_name):
    if not isinstance(folder_name, str):
        raise TypeError('{} is not a valid folder name'.format(folder_name))
    if os.path.isdir(folder_name):
        logger.info('[{}] already exist'.format(folder_name))
        return folder_name
    else:
        try:
            os.mkdir(folder_name)
            logger.info('[{}] has been created'.format(folder_name))
            return folder_name
        except FileExistsError:
            raise
        else:
            raise

def _get_full_path(d=None):
    if d is None:
        return os.getcwd()
    else:
        return os.path.join(os.getcwd(), d)

def _delete_older_files(wf, no_of_days):
    logger.info('Delete old logs/scripts in [{}]'.format(_get_full_path(wf)))
    logger.info('Delete old logs/scripts [{}] days before'.format(no_of_days))
    pass

def get_all_jobs():
    # TODO: to be implemented with db connection
    j1 = Job(1,'Job 1','job1@gmail.com')
    j2 = Job(2,'Job 2','job2@gmail.com')
    j3 = Job(3,'Job 3','job3@gmail.com') # no steps
    return [j1,j2,j3]

def get_all_steps():
    # TODO: to be implemented with db connection
    s1 = Step(1,1,'j1_s1.bteq',10)
    s2 = Step(1,2,'j1_s2.bteq',20)
    s3 = Step(2,3,'j2_s1.bteq',10)
    s4 = Step(2,4,'j2_s2.bteq',20)
    return [s1,s2,s3,s4]

def get_all_params():
    # TODO: to be implemented with db connection
    p1 = Param(1,'param1','v_param1')
    p2 = Param(1,'param2','v_param2')
    p3 = Param(2,'paramy','v_param1')
    p4 = Param(2,'paramx','v_param1')
    p5 = Param(3,'param1','v_param1')
    p6 = Param(3,'param1','v_param1')
    p7 = Param(4,'param1','v_param1')
    p8 = Param(4,'param1','v_param1')
    return [p1,p2,p3,p4,p5,p6,p7,p8]



def _check_job_files(lib_folder, files):
    if isinstance(files, str):
        return os.path.isfile(os.path.join(lib_folder, files))
    elif isinstance(files, list):
        r = True
        for item in files:
            logger.debug('check {}'.format(os.path.join(lib_folder, item)))
            if not os.path.isfile(os.path.join(lib_folder, item)):
                r = False
                break
            else:
                pass
        return r
    else:
        raise TypeError('files must be a str or list')

def build_job_def_list(lib_folder):
    jobs = get_all_jobs()
    steps = get_all_steps()
    params = get_all_params()

    job_defs = []
    for job in jobs:
        job_def = {}
        job_def['job_id'] = job.job_id
        job_def['job_name'] = job.job_name
        job_def['job_email'] = job.job_email
        job_def['steps'] = []
        for step in steps:
            if step.job_id == job.job_id:
                step_def = {}
                step_def['step_id'] = step.step_id
                step_def['seq_num'] = step.seq_num
                step_def['filename'] = step.filename
                step_def['params'] = {}
                for param in params:
                    if param.step_id == step.step_id:
                        step_def['params'][param.param_name] = param.param_value
                    else:
                        pass
                job_def['steps'].append(step_def)
            else:
                pass
        # check if the file exists before append
        logger.debug('found {}'.format(job_def))
        if len(job_def['steps']) == 0:
            logger.warning('No steps are defined for job [{}] - IGNORED'.format(job_def['job_name']))
        elif not _check_job_files(lib_folder, [x['filename'] for x in job_def['steps']]):
            logger.warning('At least one file not found for job [{}] - IGNORED'.format(job_def['job_name']))
        else:
            logger.info('New job has been added {}'.format(job_def))
            job_defs.append(job_def)
    return job_defs


def generate_scripts(username, password, lib, work, job):
    """
    Genearte all replaced bteq files and the cmd file,
    return the cmd file path
    """
    # TODO:
    dt_stamp = datetime.now().strftime("%Y%m%d_%h%mi%s")
    for s in job['steps']:
        f = s['filename']
        in_param = s['params'] # this is a dict
        in_param['username'] = username
        in_param['password'] = password

        with open(os.path.join(lib,f)) as fdin, open(os.path.join(work,f),'w') as fdout:
            text = fdin.read()
            keys_from_file = re.findall(r"\{([a-z]+?)\}", text)
            if 'username' not in keys_from_file or 'password' not in keys_from_file:
                logger.warning('password or username not found in {}'.format(f))
                continue
            fdout.write('-- This file is generated by WBTEQ at {}\n'.format(datetime.now()))
            fdout.write(text.format(**in_param))
            logger.info('Writing {} with replaced value'.format(f))

    # generate the cmd file
    cmd_file = job['job_name'].replace(' ','_') + '_' + dt_stamp + '.sh'
    log_file = job['job_name'].replace(' ','_') + '_' + dt_stamp + '.log'
    with open(os.path.join(work, cmd_file), 'w') as fcmd:
        # fcmd.write('REM This file is generated by WBTEQ at {}\n'.format(datetime.now()))
        fcmd.write('# This file is generated by WBTEQ at {}\n'.format(datetime.now()))
        for s in job['steps']:
            fcmd.write('cat < {bteq} > {log}\n'.format(bteq=s['filename'],
                                                      log=log_file))

    return os.path.join(work, cmd_file)


def get_parser():
    parser = argparse.ArgumentParser(description='BTEQ Jobs management on Windows')
    parser.add_argument('username', type=str,
                        help='The Teradata logon name for running BTEQ(s)')

    parser.add_argument('password', type=str,
                        help='The Teradata logon password for running BTEQ(s)')

    parser.add_argument('-l','--lib', default='_libs',
                        help='The library folder for WBTEQ (default _libs)',
                        action='store')

    parser.add_argument('-f','--folder', default='_wbteq',
                        help='The working folder for WBTEQ (default _wbteq)',
                        action='store')

    parser.add_argument('-d','--days', default=7,
                        help='The # of days to keep logs/scripts (default 7)',
                        action='store')

    parser.add_argument('-v', '--version', help='displays the current version of wbteq',
                        action='store_true')

    return parser


def command_line_runner():
    parser = get_parser()
    args = vars(parser.parse_args())

    if args['version']:
        print(__version__)
        return

    if not os.path.isdir(args['lib']):
        raise SystemExit('Please make sure the [{}] folder is created'.format(args['lib']))

    logger.info('The current folder is [{}]'.format(_get_full_path()))

    if _check_folder(_get_full_path(args['folder'])):
        pass
    else:
        raise ValueError('Create folder failed')

    _delete_older_files(args['folder'],args['days'])

    # build the jobs (all json format)
    # it checks of the job file exists or not
    jobs = build_job_def_list(_get_full_path(args['lib']))

    logger.info('[{}] valid job(s) has been found'.format(len(jobs)))
    for j in jobs:
        logger.info('Job name: [{}] has [{}] steps'.format(j['job_name'], len(j['steps'])))

    command_files = []
    for job in jobs:
        cmd_file = generate_scripts( args['username'],
                                     args['password'],
                                     args['lib'],
                                     args['folder'],
                                     job)
        logger.info('[{}] has been created'.format(cmd_file))
        command_files.append(cmd_file)

    for cmd in command_files:
        rcode = call([cmd])
        if rcode == 0:
            logger.info('Calling {} successful'.format(cmd))
        else:
            logger.warning('Failed to call {}'.format(cmd))


if __name__ == '__main__':
    command_line_runner()
