import os
import shutil
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.filesystems import AbstractedFS

# ── Configuration ────────────────────────────────────────────────────────────

FTP_ROOT    = r"FTP"   # Root directory (symlinks would be created here)
FTP_HOST    = "0.0.0.0"
FTP_PORT    = 2121
USERNAME    = "user"
PASSWORD    = "pass"

# ── Symlink-aware filesystem ──────────────────────────────────────────────────

class SymlinkAwareFS(AbstractedFS):
    """
    Overrides validpath() so that symlinks placed directly inside the FTP root
    are allowed even when their targets resolve to a path outside the root.
    """

    def validpath(self, path: str) -> bool:
        # normpath resolves ".." and "." (blocks traversal attacks) but does
        # NOT follow symlinks — so files inside a symlinked folder still appear
        # to live under the root and pass validation.
        root = os.path.normpath(self.root)
        norm = os.path.normpath(path)
        return norm.startswith(root)

# ── Handler with SITE DF (disk usage) ─────────────────────────────────────────

class DiskUsageFTPHandler(FTPHandler):
    """
    Adds "SITE DF [<SP> path]", which reports the disk usage of the drive
    behind an FTP path (current directory if omitted). Symlinks are followed,
    so every symlinked folder reports its own drive.

    Reply: 213 total=<bytes> used=<bytes> free=<bytes> path=<ftp path>
    """

    proto_cmds = dict(FTPHandler.proto_cmds)
    proto_cmds["SITE DF"] = dict(
        perm="l",
        auth=True,
        arg=None,
        help="Syntax: SITE DF [<SP> path] (show disk usage in bytes).",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._extra_feats = self._extra_feats + ["SITE DF"]

    def ftp_SITE_HELP(self, line):
        if line and not line.upper().startswith("SITE "):
            line = "SITE " + line
        return super().ftp_SITE_HELP(line)

    def ftp_SITE_DF(self, path):
        try:
            real = os.path.realpath(path)
            if os.path.isfile(real):
                real = os.path.dirname(real)
            usage = self.run_as_current_user(shutil.disk_usage, real)
        except OSError as err:
            self.respond(f"550 {err.strerror or err}.")
            return
        self.respond(
            f"213 total={usage.total} used={usage.used} free={usage.free} "
            f"path={self.fs.fs2ftp(path)}"
        )

# ── Server setup ──────────────────────────────────────────────────────────────

def main():
    authorizer = DummyAuthorizer()
    authorizer.add_user(USERNAME, PASSWORD, FTP_ROOT, perm="elradfmwMT")
    # Permissions: e=change dir, l=list, r=read, a=append, d=delete,
    #              f=rename, m=mkdir, w=write, M=chmod, T=mtime

    handler = DiskUsageFTPHandler
    handler.authorizer= authorizer
    handler.abstracted_fs = SymlinkAwareFS

    server = FTPServer((FTP_HOST, FTP_PORT), handler)
    print(f"Serving {FTP_ROOT} on {FTP_HOST}:{FTP_PORT}")
    print(f"Login: {USERNAME} / {PASSWORD}")
    server.serve_forever()

if __name__ == "__main__":
    if not os.path.isdir(FTP_ROOT):
        os.makedirs(FTP_ROOT)

    main()