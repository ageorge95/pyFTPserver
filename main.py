import os
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

# ── Server setup ──────────────────────────────────────────────────────────────

def main():
    authorizer = DummyAuthorizer()
    authorizer.add_user(USERNAME, PASSWORD, FTP_ROOT, perm="elradfmwMT")
    # Permissions: e=change dir, l=list, r=read, a=append, d=delete,
    #              f=rename, m=mkdir, w=write, M=chmod, T=mtime

    handler = FTPHandler
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