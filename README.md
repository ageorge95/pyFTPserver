# pyFTPserver
Simple python FTP server with symlink support on windows.

# Connection limits
`MAX_CONS` (default 64) and `MAX_CONS_PER_IP` (default 10) in `main.py` cap the number of simultaneous connections,
so clients using parallel transfers cannot overload the server. Extra connections are refused with
`421 Too many connections ...`.

# Disk usage (`SITE DF`)
The server adds a custom command that reports disk space for the drive behind an FTP path:

```
SITE DF [<SP> path]
```

- `path` is optional. Without it, the current directory is used. It can be relative or absolute, and it can point to a file.
- Symlinks and junctions are followed, so each symlinked folder (e.g. `/share1`, `/share2`) reports its own drive.
- You must be logged in and have the `l` (list) permission.
- `FEAT` lists `SITE DF`, so clients can check for support.

Replies (all values are in bytes):

```
213 total=4000787030016 used=1234567890 free=3999552462126 path=/share1
550 <error message>.          (path does not exist / cannot be read)
550 Not enough privileges.
530 Log in with USER and PASS first.
500 Command "SITE DF" not understood.   (server without this feature)
```

Example with Python's `ftplib`:

```python
resp = ftp.sendcmd("SITE DF /share1")
info = dict(kv.split("=", 1) for kv in resp[4:].split(" ", 3))
total, used, free = int(info["total"]), int(info["used"]), int(info["free"])
```

`path` is always the last field and may contain spaces.

# Support
Found this project useful? Send your ❤ in any form you can 🙂. Please contact me if you donated and want to be added to the contributors list !

- chia XCH---xch1glz7ufrfw9xfp5rnlxxh9mt9vk9yc8yjseet5c6u0mmykq8cpseqna6494
