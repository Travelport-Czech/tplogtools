#!/usr/bin/env python3
"""Unit-tests for logrotlib"""

import unittest
from unittest import mock
import logging
from pathlib import Path
import tempfile
import io
import datetime
from tplogtools.logrotlib import human_size_units_to_base, need_to_rotate_log
from tplogtools.logrotlib import process_log, run_compressors, get_spec_config
from tplogtools.logrotlib import process_path

class TestLogrotlib(unittest.TestCase):
    """Main test class"""

    def test_need_to_rotate_log(self):
        """Test of function choosing if log rotation is needed"""
        self.assertTrue(need_to_rotate_log(0, 20, 'daily', 15, 'daily'), 'rotate log by time')
        self.assertFalse(need_to_rotate_log(10, 20, 'daily', 15, 'hourly'), 'do not rotate log by time')
        self.assertTrue(need_to_rotate_log(10, 20, 'daily', 25, None), 'rotate log by max size')
        self.assertFalse(need_to_rotate_log(10, 20, 'hourly', 5, 'hourly'), 'do not rotate log by min size')

    def test_human_size_units_to_base(self):
        """Test of conversion human like file size units to integer"""
        self.assertEqual(human_size_units_to_base(1), 1)
        self.assertEqual(human_size_units_to_base('1'), 1)
        self.assertEqual(human_size_units_to_base('1b'), 1)
        self.assertEqual(human_size_units_to_base('1k'), 1000)
        self.assertEqual(human_size_units_to_base('1kb'), 1000)
        self.assertEqual(human_size_units_to_base('1kib'), 1024)
        self.assertEqual(human_size_units_to_base('1KiB'), 1024)
        self.assertEqual(human_size_units_to_base('1KiB 1b'), 1025)
        self.assertEqual(human_size_units_to_base('1M'), 1000000)
        self.assertEqual(human_size_units_to_base('1Mi'), 1024*1024)
        self.assertEqual(human_size_units_to_base('1G'), 1000000000)
        self.assertEqual(human_size_units_to_base('1T'), 1000000000000)
        self.assertRaisesRegex(ValueError, 'Bad unit "a" in size parameter "1a".', human_size_units_to_base, '1a')

    def test_process_log_without_configuration(self):
        """Tests of try rotation without configuration"""
        with mock.patch('sys.stdout', new=io.StringIO()) as fake_stdout:
            compressors = process_log(
                datetime.datetime(year=2019, month=1, day=10, hour=21, minute=30),
                {},
                'hourly',
                '/tmp/pokus.log',
                10
            )
            self.assertEqual(compressors, [])
            self.assertEqual(fake_stdout.getvalue(), 'Checking "/tmp/pokus.log"... rotation not needed.\n')

    def test_process_log_without_target_configuration(self):
        """Tests of try rotation without configuration"""
        with mock.patch('sys.stdout', new=io.StringIO()) as fake_stdout:
            compressors = process_log(
                datetime.datetime(year=2019, month=1, day=10, hour=21, minute=30),
                {'max_size': 0},
                'hourly',
                '/tmp/pokus.log',
                10
            )
            self.assertEqual(compressors, [])
            self.assertEqual(fake_stdout.getvalue(), 'Checking "/tmp/pokus.log"... missing target in configuration.\n')

    def test_process_log_with_ignore_in_configuration(self):
        """Tests of try rotation with ignore in configuration"""
        with mock.patch('sys.stdout', new=io.StringIO()) as fake_stdout:
            compressors = process_log(
                datetime.datetime(year=2019, month=1, day=10, hour=21, minute=30),
                {'ignore': True},
                'hourly',
                '/tmp/pokus.log',
                10
            )
            self.assertEqual(compressors, [])
            self.assertEqual(fake_stdout.getvalue(), '')

    def test_process_log_with_min_size_in_configuration(self):
        """Tests of try rotation with min_size in configuration"""
        with tempfile.TemporaryDirectory() as sandbox:
            with mock.patch('sys.stdout', new=io.StringIO()) as fake_stdout:
                srcfile = Path(sandbox, 'pokus.log')
                srcfile.touch()
                destfile = Path(sandbox, 'backup', 'pokus.log')
                compressors = process_log(
                    datetime.datetime(year=2019, month=1, day=10, hour=21, minute=30),
                    {'target': '{{path}}/backup/{{name}}.{{ext}}', 'interval': 'hourly', 'min_size': 15},
                    'hourly',
                    str(srcfile),
                    10
                )
                self.assertEqual(compressors, [])
                self.assertTrue(srcfile.exists())
                self.assertFalse(destfile.exists())
                self.assertEqual(fake_stdout.getvalue(), 'Checking "{src}"... rotation not needed.\n'.format(src=srcfile))

    def test_process_log_with_target_in_configuration(self):
        """Tests of try rotation with target and interval in configuration"""
        with tempfile.TemporaryDirectory() as sandbox:
            with mock.patch('sys.stdout', new=io.StringIO()) as fake_stdout:
                srcfile = Path(sandbox, 'pokus.log')
                srcfile.touch()
                destfile = Path(sandbox, 'backup', 'pokus-20190110-2130.log')
                compressors = process_log(
                    datetime.datetime(year=2019, month=1, day=10, hour=21, minute=30),
                    {'target': '{{path}}/backup/{{name}}-%Y%m%d-%H%M.{{ext}}', 'interval': 'hourly'},
                    'hourly',
                    str(srcfile),
                    10
                )
                self.assertEqual(compressors, [])
                self.assertFalse(srcfile.exists())
                self.assertTrue(destfile.exists())
                self.assertEqual(fake_stdout.getvalue(), 'Checking "{src}"... rotating... "{src}" -> "{dest}" done.\n'.format(src=srcfile, dest=destfile))

    def test_process_log_with_relative_target_in_configuration(self):
        """Tests of try rotation with relative target and interval in configuration"""
        with tempfile.TemporaryDirectory() as sandbox:
            with mock.patch('sys.stdout', new=io.StringIO()) as fake_stdout:
                srcfile = Path(sandbox, 'pokus.log')
                srcfile.touch()
                destfile = Path(sandbox, 'backup', 'pokus.log')
                compressors = process_log(
                    datetime.datetime(year=2019, month=1, day=10, hour=21, minute=30),
                    {'target': 'backup/{{name}}.{{ext}}', 'interval': 'hourly'},
                    'hourly',
                    str(srcfile),
                    10
                )
                self.assertEqual(compressors, [])
                self.assertFalse(srcfile.exists())
                self.assertTrue(destfile.exists())
                self.assertEqual(fake_stdout.getvalue(), 'Checking "{src}"... rotating... "{src}" -> "{dest}" done.\n'.format(src=srcfile, dest=Path('backup', 'pokus.log')))

    def test_process_log_with_compress_in_configuration(self):
        """Tests of try rotation with compress in configuration"""
        with tempfile.TemporaryDirectory() as sandbox:
            with mock.patch('sys.stdout', new=io.StringIO()) as fake_stdout:
                srcfile = Path(sandbox, 'pokus.log')
                srcfile.touch()
                destfile = Path(sandbox, 'backup', 'pokus.log')
                compressors = process_log(
                    datetime.datetime(year=2019, month=1, day=10, hour=21, minute=30),
                    {
                        'target': '{{path}}/backup/{{name}}.{{ext}}',
                        'interval': 'hourly',
                        'compress': 'gzip -9'
                    },
                    'hourly',
                    str(srcfile),
                    10
                )
                self.assertEqual(compressors, [[sandbox, 'gzip', '-9', str(destfile)]])
                self.assertFalse(srcfile.exists())
                self.assertTrue(destfile.exists())
                self.assertEqual(fake_stdout.getvalue(), 'Checking "{src}"... rotating... "{src}" -> "{dest}" done.\n'.format(src=srcfile, dest=destfile))

    def test_process_log_with_exec_pre_in_configuration(self):
        """Tests of try rotation with exec_pre in configuration"""
        with tempfile.TemporaryDirectory() as sandbox:
            with mock.patch('sys.stderr', new=io.StringIO()) as fake_stderr:
                with mock.patch('sys.stdout', new=io.StringIO()) as fake_stdout:
                    stream_handler = logging.StreamHandler(fake_stderr)
                    logging.getLogger().addHandler(stream_handler)
                    try:
                        srcfile = Path(sandbox, 'pokus.log')
                        srcfile.touch()
                        destfile = Path(sandbox, 'backup', 'pokus.log')
                        compressors = process_log(
                            datetime.datetime(year=2019, month=1, day=10, hour=21, minute=30),
                            {
                                'target': '{{path}}/backup/{{name}}.{{ext}}',
                                'interval': 'hourly',
                                'compress': 'bzip2',
                                'exec_pre': '/bin/false'
                            },
                            'hourly',
                            str(srcfile),
                            10
                        )
                    finally:
                        logging.getLogger().removeHandler(stream_handler)
                    self.assertEqual(compressors, [])
                    self.assertTrue(srcfile.exists())
                    self.assertFalse(destfile.exists())
                    self.assertEqual(fake_stdout.getvalue(), 'Checking "{src}"... exec_pre failed.\n'.format(src=srcfile))
                    self.assertEqual(fake_stderr.getvalue(), 'exec_pre "/bin/false pokus.log" failed with code 1\n')

    def test_process_log_with_exec_post_in_configuration(self):
        """Tests of try rotation with exec_post in configuration"""
        with tempfile.TemporaryDirectory() as sandbox:
            with mock.patch('sys.stderr', new=io.StringIO()) as fake_stderr:
                with mock.patch('sys.stdout', new=io.StringIO()) as fake_stdout:
                    stream_handler = logging.StreamHandler(fake_stderr)
                    logging.getLogger().addHandler(stream_handler)
                    try:
                        srcfile = Path(sandbox, 'pokus.log')
                        srcfile.touch()
                        destfile = Path(sandbox, 'backup', 'pokus.log')
                        compressors = process_log(
                            datetime.datetime(year=2019, month=1, day=10, hour=21, minute=30),
                            {
                                'target': '{{path}}/backup/{{name}}.{{ext}}',
                                'interval': 'hourly',
                                'compress': 'bzip2',
                                'exec_post': '/bin/false'
                            },
                            'hourly',
                            str(srcfile),
                            10
                        )
                    finally:
                        logging.getLogger().removeHandler(stream_handler)
                    self.assertEqual(compressors, [])
                    self.assertFalse(srcfile.exists())
                    self.assertTrue(destfile.exists())
                    self.assertEqual(fake_stdout.getvalue(), 'Checking "{src}"... rotating... "{src}" -> "{dest}" exec_post failed.\n'.format(src=srcfile, dest=destfile))
                    self.assertEqual(fake_stderr.getvalue(), 'exec_post "/bin/false {dest}" failed with code 1\n'.format(dest=destfile))

    def test_process_log_with_pre_and_post_in_configuration(self):
        """Tests of try rotation with positive pre and post exec in configuration"""
        with tempfile.TemporaryDirectory() as sandbox:
            with mock.patch('sys.stdout', new=io.StringIO()) as fake_stdout:
                srcfile = Path(sandbox, 'pokus.log')
                srcfile.touch()
                destfile = Path(sandbox, 'backup', 'pokus.log')
                compressors = process_log(
                    datetime.datetime(year=2019, month=1, day=10, hour=21, minute=30),
                    {
                        'target': '{{path}}/backup/{{name}}.{{ext}}',
                        'interval': 'hourly',
                        'compress': 'gzip -9',
                        'exec_pre': '/bin/true',
                        'exec_post': '/bin/true'
                    },
                    'hourly',
                    str(srcfile),
                    10
                )
                self.assertEqual(compressors, [[sandbox, 'gzip', '-9', str(destfile)]])
                self.assertFalse(srcfile.exists())
                self.assertTrue(destfile.exists())
                self.assertEqual(fake_stdout.getvalue(), 'Checking "{src}"... rotating... "{src}" -> "{dest}" done.\n'.format(src=srcfile, dest=destfile))

    def test_process_log_with_target_exists(self):
        """Tests of try rotation with target exists"""
        with tempfile.TemporaryDirectory() as sandbox:
            with mock.patch('sys.stdout', new=io.StringIO()) as fake_stdout:
                srcfile = Path(sandbox, 'pokus.log')
                srcfile.touch()
                destfile = Path(sandbox, 'backup', 'pokus.log')
                destfile.mkdir(parents=True)
                compressors = process_log(
                    datetime.datetime(year=2019, month=1, day=10, hour=21, minute=30),
                    {
                        'target': '{{path}}/backup/{{name}}.{{ext}}',
                        'interval': 'hourly',
                        'compress': 'gzip -9',
                    },
                    'hourly',
                    str(srcfile),
                    10
                )
                self.assertEqual(compressors, [])
                self.assertTrue(srcfile.exists())
                self.assertTrue(destfile.exists())
                self.assertEqual(fake_stdout.getvalue(), 'Checking "{src}"... rotating... "{src}" -> "{dest}" target already exists!\n'.format(src=srcfile, dest=destfile))

    def test_process_log_with_os_error_at_move(self):
        """Tests of try rotation with OS error while file move"""
        with tempfile.TemporaryDirectory() as sandbox:
            with mock.patch('sys.stdout', new=io.StringIO()) as fake_stdout:
                with self.assertLogs() as logger:
                    srcfile = Path(sandbox, 'pokus.log')
                    srcfile.touch()
                    destpath = Path(sandbox, 'backup')
                    destpath.touch()
                    compressors = process_log(
                        datetime.datetime(year=2019, month=1, day=10, hour=21, minute=30),
                        {
                            'target': '{{path}}/backup/{{name}}.{{ext}}',
                            'interval': 'hourly',
                            'compress': 'gzip -9',
                        },
                        'hourly',
                        str(srcfile),
                        10
                    )
                self.assertEqual(compressors, [])
                self.assertTrue(srcfile.exists())
                self.assertEqual(fake_stdout.getvalue(), 'Checking "{src}"... rotating... '.format(src=srcfile))
                self.assertIn("FileExistsError: [Errno 17] File exists: '{}'".format(destpath), logger.output[0])

    def test_process_path(self):
        """Test process_path method"""
        with tempfile.TemporaryDirectory() as sandbox:
            with mock.patch('sys.stdout', new=io.StringIO()) as fake_stdout:
                linked_file = Path(sandbox, 'linked_file.log')
                linked_file.touch()
                link_file = Path(sandbox, 'link_file.log')
                link_file.symlink_to(linked_file)
                directory = Path(sandbox, 'directory.log')
                directory.mkdir()
                regular_file = Path(sandbox, 'regular_file.log')
                regular_file.touch()
                dest_linked_file = Path(sandbox, 'backup', 'linked_file.log')
                dest_regular_file = Path(sandbox, 'backup', 'regular_file.log')
                compressors = process_path(
                    datetime.datetime(year=2019, month=1, day=10, hour=21, minute=30),
                    {'defaults': {
                        'target': '{{path}}/backup/{{name}}.{{ext}}',
                        'interval': 'hourly',
                        'compress': 'bzip2',
                        'min_size': 0
                    }},
                    'hourly',
                    sandbox
                )
                self.assertEqual(compressors, [
                    [sandbox, 'bzip2', str(dest_linked_file)],
                    [sandbox, 'bzip2', str(dest_regular_file)]
                ])
                self.assertFalse(linked_file.exists())
                self.assertFalse(regular_file.exists())
                self.maxDiff = 1024
                self.assertEqual(
                    fake_stdout.getvalue(),
                    'Checking "{src}"... rotating... "{src}" -> "{dest}" done.\n'.format(src=linked_file, dest=dest_linked_file) + \
                    'Checking "{src}"... rotating... "{src}" -> "{dest}" done.\n'.format(src=regular_file, dest=dest_regular_file)
                )

    def test_run_compressors(self):
        """Test run_compressors method"""
        with tempfile.TemporaryDirectory() as sandbox:
            with mock.patch('sys.stdout', new=io.StringIO()) as fake_stdout:
                firstfile = Path(sandbox, 'first.log')
                firstfile.touch()
                secondfile = Path(sandbox, 'second.log')
                secondfile.touch()
                run_compressors(
                    [
                        [str(sandbox), 'false'],
                        [str(sandbox), 'gzip', '-9', str(firstfile)],
                        [str(sandbox), 'gzip', '-9', str(secondfile)]
                    ]
                )
                self.assertEqual(fake_stdout.getvalue(), 'Executing compressors... done.\n')
                self.assertFalse(firstfile.exists())
                self.assertFalse(secondfile.exists())
                self.assertTrue(firstfile.with_suffix('.log.gz').exists())
                self.assertTrue(secondfile.with_suffix('.log.gz').exists())

    def test_run_compressors_bad(self):
        """Test run_compressors method"""
        with tempfile.TemporaryDirectory() as sandbox:
            with mock.patch('sys.stdout', new=io.StringIO()) as fake_stdout:
                with self.assertLogs() as logger:
                    firstfile = Path(sandbox, 'first.log')
                    firstfile.touch()
                    secondfile = Path(sandbox, 'second.log')
                    secondfile.touch()
                    bad_gzip = Path(sandbox, 'gzip')
                    run_compressors(
                        [
                            [str(sandbox), 'false'],
                            [str(sandbox), str(bad_gzip), '-9', str(firstfile)],
                            [str(sandbox), 'gzip', '-9', str(secondfile)]
                        ]
                    )
                self.assertEqual(fake_stdout.getvalue(), 'Executing compressors... done.\n')
                self.assertTrue(firstfile.exists())
                self.assertFalse(secondfile.exists())
                self.assertFalse(firstfile.with_suffix('.log.gz').exists())
                self.assertTrue(secondfile.with_suffix('.log.gz').exists())
                self.assertIn("FileNotFoundError: [Errno 2] No such file or directory: '{}'".format(bad_gzip), logger.output[0])

    def test_get_spec_config_empty(self):
        """Test get_spec_config on empty conf"""
        spec_conf = get_spec_config({}, '')
        self.assertEqual(spec_conf, {})

    def test_get_spec_config_defaults(self):
        """Test get_spec_config on conf with defaults"""
        spec_conf = get_spec_config({
            'defaults': {
                'foo': 'bar'
            }
        }, '')
        self.assertEqual(spec_conf, {'foo': 'bar'})

    def test_get_spec_config_match(self):
        """Test get_spec_config on matching conf"""
        spec_conf = get_spec_config({
            'defaults': {
                'default_foo': 'default_bar',
                'foo': 'bar'
            },
            'specific': [
                {'mask': ['filenomatch'], 'foo': 'bar_nomatch'},
                {'mask': ['filematch'], 'foo': 'match'},
                {'mask': ['filenomatch2'], 'foo': 'bar_nomatch2'}
            ]
        }, 'filematch')
        self.assertEqual(spec_conf, {'default_foo': 'default_bar', 'foo': 'match', 'mask': ['filematch']})

    def test_get_spec_config_immutability(self):
        """Test get_spec_config immutability"""
        conf = {
            'defaults': {
                'default_foo': 'default_bar',
                'foo': 'bar'
            },
            'specific': [
                {'mask': ['filenomatch'], 'foo': 'bar_nomatch'},
                {'mask': ['filematch'], 'foo': 'match'},
                {'mask': ['filenomatch2'], 'foo': 'bar_nomatch2'}
            ]
        }
        get_spec_config(conf, 'filematch')
        self.assertEqual(conf['defaults'], {'default_foo': 'default_bar', 'foo': 'bar'})
