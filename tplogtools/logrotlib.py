#!/usr/bin/env python3
"""Unit-tested functions for logrot"""

import os
import stat
import fnmatch
import logging
import shutil
import shlex
import subprocess

def need_to_rotate_log(min_size, max_size, max_time_interval, log_size, time_interval):
    """Check if log match criteria for rotation"""
    return log_size >= max_size or (time_interval == max_time_interval and log_size >= min_size)

def human_size_units_to_base(human):
    """Covert TB, GB, MB etc to bytes"""
    amount = 0
    local_amount = 0
    unit = ''
    for char in str(human):
        if char == ' ':
            pass
        elif char in '0123456789':
            if unit:
                amount += local_amount * unit_to_multiplier(unit, human)
                unit = ''
                local_amount = 0
            local_amount = local_amount * 10 + int(char)
        else:
            unit += char
    if local_amount:
        amount += local_amount * unit_to_multiplier(unit, human)
    return amount

UNITS = {'': 0, 'K': 1, 'M': 2, 'G': 3, 'T': 4}

def unit_to_multiplier(unit, human):
    """Convert text multiplier to numeric i.e. 'K' to 1000"""
    norm_unit = unit.upper().rstrip('B')
    if norm_unit.endswith('I'):
        base = 1024
        norm_unit = norm_unit[:-1]
    else:
        base = 1000
    if norm_unit in UNITS:
        return base ** UNITS[norm_unit]
    raise ValueError('Bad unit "{}" in size parameter "{}".'.format(unit, human))

class ChDir:
    """Contextmanager for running code with specified path as cwd"""
    def __init__(self, new_pwd):
        self.new_pwd = new_pwd
        self.old_pwd = None

    def __enter__(self):
        self.old_pwd = os.getcwd()
        os.chdir(self.new_pwd)

    def __exit__(self, *args):
        os.chdir(self.old_pwd)

def process_path(now, conf, interval, path):
    """Process all files on given path"""
    compressors = []
    for filename in os.listdir(path):
        fullname = os.path.join(path, filename)
        filestat = os.stat(fullname, follow_symlinks=False)
        if stat.S_ISREG(filestat.st_mode):
            compressors += process_log(
                now,
                get_spec_config(conf, filename),
                interval,
                fullname,
                filestat.st_size
            )
    return compressors

def get_spec_config(conf, filename):
    """Return configuration specific for given filename"""
    spec_config = conf.get('defaults', {}).copy()
    for spec_def in conf.get('specific', []):
        if name_match_masks(filename, spec_def.get('mask', [])):
            spec_config.update(spec_def)
    return spec_config

def name_match_masks(filename, masks):
    """Check if filename match to any from given mask"""
    for mask in masks:
        if fnmatch.fnmatch(filename, mask):
            return True
    return False

def process_log(now, spec_config, interval, fullname, filesize):
    """Process one given file"""
    if spec_config.get('ignore', False):
        return []
    compressors = []
    print('Checking "{}"...'.format(fullname), end=' ', flush=True)
    if need_to_rotate_log(
                human_size_units_to_base(spec_config.get('min_size', '0')),
                human_size_units_to_base(spec_config.get('max_size', '2T')),
                spec_config.get('interval', None),
                filesize,
                interval
        ):
        path, filename = os.path.split(fullname)
        target = compose_target(now, path, filename, spec_config.get('target', ''))
        with ChDir(path) as _:
            exec_pre = spec_config.get('exec_pre', '')
            if exec_pre:
                if not run_pre(exec_pre, filename):
                    return []
            if target:
                print('rotating...', end=' ', flush=True)
                try:
                    os.makedirs(os.path.dirname(target), exist_ok=True)
                    print('"{}" -> "{}"'.format(fullname, target), end=' ', flush=True)
                    if os.path.exists(target):
                        print('target already exists!', flush=True)
                        return []
                    shutil.move(fullname, target)
                    exec_post = spec_config.get('exec_post', '')
                    if exec_post:
                        if not run_post(exec_post, target):
                            return []
                    print('done.', flush=True)
                    compressor = spec_config.get('compress', '')
                    if compressor:
                        compressors.append([path] + shlex.split(compressor) + [target])
                except OSError as exception:
                    logging.exception(exception)
            else:
                print('missing target in configuration.', flush=True)
    else:
        print('rotation not needed.', flush=True)
    return compressors

def compose_target(now, path, filename, template):
    """Fill target template by filename components and given timestamp"""
    basename, extension = os.path.splitext(filename)
    timed_target = now.strftime(template)
    return timed_target \
            .replace('{{path}}', path) \
            .replace('{{name}}', basename) \
            .replace('{{ext}}', extension.lstrip('.'))

def run_pre(exec_pre, filename):
    """Run exec_pre before log moved"""
    exec_pre_cmd = shlex.split(exec_pre) + [filename]
    logging.debug('exec_pre "%s"', ' '.join(exec_pre_cmd))
    exec_pre_result = subprocess.run(exec_pre_cmd, check=False)
    if exec_pre_result.returncode != 0:
        print('exec_pre failed.', flush=True)
        logging.warning(
            'exec_pre "%s" failed with code %d',
            ' '.join(exec_pre_cmd),
            exec_pre_result.returncode
        )
        return False
    return True

def run_post(exec_post, target):
    """Run exec_post after log moved"""
    exec_post_cmd = shlex.split(exec_post) + [target]
    logging.debug('exec_post "%s"', ' '.join(exec_post_cmd))
    exec_post_result = subprocess.run(exec_post_cmd, check=False)
    if exec_post_result.returncode != 0:
        print('exec_post failed.', flush=True)
        logging.warning(
            'exec_post "%s" failed with code %d',
            ' '.join(exec_post_cmd),
            exec_post_result.returncode
        )
        return False
    return True

def run_compressors(compressors):
    """Exec compression precesses after rotation all files"""
    os.nice(10)
    print('Executing compressors...', end=' ', flush=True)
    for compressor in compressors:
        try:
            subprocess.run(compressor[1:], cwd=compressor[0], check=False)
        except OSError as exception:
            logging.exception(exception)
    print('done.', flush=True)
