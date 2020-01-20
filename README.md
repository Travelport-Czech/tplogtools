# tplogtools

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
