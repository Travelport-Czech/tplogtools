# tplogtools

- [logclean](#logclean) - Removes old files from the specified paths according to the criteria of the limits.
- [stdout2log](#stdout2log) - Tool for store stdin to rotated file.
- [logtime](#logtime) - Inserts the current time before each input line
- [logrot](#logrot) - Move big or overtimed logs to backup

## logclean

```
logclean [{-n|--dry-run}] [{-f|--force}] [limits] path...

Removes old files from the specified paths according to the criteria of the limits.
The meaning of the parameter is:
  -n, --dry-run                    no file will be deleted, the tool will only list what it would do
  -f, --force                      ignores if any of the specified paths does not exist
                                   (applicable to logclean -f /tmp/a.* when it does not throw an error, even if file matching the mask in /tmp is not)
Limits are defined by parameters (separated by space integer value after each parameter):
  -p, --min-free-space-on-device   defines how many percent of the block device on which the scanned files are to remain free
                                   (default: 0)
  -c, --min-files-per-group        the number of the most recent files in each group that will never be deleted
                                   (default: 0)
  -m, --min-file-age               the number of days the file will not be deleted even if there is not enough free space left on the device
                                   (default: 0)
  -t, --max-file-age               the number of days after which the file will be deleted, even if there is enough space left on the device
                                   (default: 99999)
```

For example, if you want to delete all files from the old-logs directory, older than 10 days:
```
  logclean -t 10 old-logs
```

if we want to keep at least 3 files of each type:
```
  logclean -t 10 -c 3 old-logs
```

if we want to keep at least 10 % of free space on the log disc, but we also need history for at least 3 days:
```
  logclean -p 10 -m 3 old-logs
```

## stdout2log
```
usage: stdout2log [-h] -t TIME [-s SIZE] -b BACKUP [-c COMPRESS] filename

Tool for store stdin to rotated file.

positional arguments:
  filename              Live log filename.

optional arguments:
  -h, --help            show this help message and exit
  -t TIME, --time TIME  Time to rotation in form HH:MM
  -s SIZE, --size SIZE  Max size of live log in MiB
  -b BACKUP, --backup BACKUP
                        Mask for rotated log filename
  -c COMPRESS, --compress COMPRESS
                        Command for compression of rotated log
```

## logtime
```
usage: logtime [-h]

Inserts the current time before each input line

optional arguments:
  -h, --help  show this help message and exit
```

Example:
```
$ tar czvf sample.tgz /usr/share | ./logtime 
2020-01-21T12:13:17.075558+01:00 /usr/share/
2020-01-21T12:13:17.190862+01:00 /usr/share/aclocal/
2020-01-21T12:13:17.190948+01:00 /usr/share/aclocal/libtool.m4
2020-01-21T12:13:18.101484+01:00 /usr/share/aclocal/inttypes_h.m4
2020-01-21T12:13:18.193696+01:00 /usr/share/aclocal/wchar_t.m4
2020-01-21T12:13:18.337082+01:00 /usr/share/aclocal/lib-prefix.m4
2020-01-21T12:13:18.654403+01:00 /usr/share/aclocal/ltdl.m4
2020-01-21T12:13:18.756979+01:00 /usr/share/aclocal/lib-link.m4
2020-01-21T12:13:18.825651+01:00 /usr/share/aclocal/glib-gettext.m4
2020-01-21T12:13:18.864213+01:00 /usr/share/aclocal/progtest.m4
...
```

## logrot
```

usage: logrot [-h] -c CONF [--hourly | --daily] path [path ...]

Move big or overtimed logs to backup

positional arguments:
  path                  Path to folder with log

optional arguments:
  -h, --help            show this help message and exit
  -c CONF, --conf CONF  Path to config yml file
  --hourly              Use rules configured as "hourly"
  --daily               Use rules configured as "daily"
```

Config sample:
```
defaults:
  ignore: False
  min_size: 1M
  max_size: 4G
  interval: daily
  exec_pre: ''
  exec_post: ''
  target: '{{path}}/oldlogs/{{name}}-%Y%m%d-%H:%M.{{ext}}'
  compress: 'bzip2'
specific:
  - mask:
    - httpd-*.log
    - nginx_*.log
    - php_*.log
    - console.log
    ignore: True
  - mask:
    - logfile.log
    exec_post: 'sendHupToFileUsers ao3Restart'
    interval: hourly
    min_size: 500M
```
