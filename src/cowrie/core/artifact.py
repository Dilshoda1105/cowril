# Copyright (c) 2016 Michel Oosterhof <michel@oosterhof.net>

"""
This module contains code to handling saving of honeypot artifacts
These will typically be files uploaded to the honeypot and files
downloaded inside the honeypot, or input being piped in.

Code behaves like a normal Python file handle.

Example:

    with Artifact(name) as f:
        f.write("abc")

or:

    g = Artifact("testme2")
    g.write("def")
    g.close()

"""

from __future__ import annotations

import hashlib
import os
import tempfile
from types import TracebackType
from typing import Any, Optional, Tuple, Type

from twisted.python import log

from cowrie.core.config import CowrieConfig


class Artifact:

    artifactDir: str = CowrieConfig.get("honeypot", "download_path")

    def __init__(self, label: str) -> None:
        self.label: str = label

        self.fp = tempfile.NamedTemporaryFile(dir=self.artifactDir, delete=False)
        self.tempFilename = self.fp.name
        self.closed: bool = False

        self.shasum: str = ""
        self.shasumFilename: str = ""

    def __enter__(self) -> Any:
        return self.fp

    def __exit__(
        self,
        etype: Optional[Type[BaseException]],
        einst: Optional[BaseException],
        etrace: Optional[TracebackType],
    ) -> bool:
        self.close()
        return True

    def write(self, bytes: bytes) -> None:
        self.fp.write(bytes)

    def fileno(self) -> Any:
        return self.fp.fileno()

    def close(self, keepEmpty: bool = False) -> Optional[Tuple[str, str]]:
        size: int = self.fp.tell()
        if size == 0 and not keepEmpty:
            os.remove(self.fp.name)
            return None

        self.fp.seek(0)
        data = self.fp.read()
        self.fp.close()
        self.closed = True

        self.shasum = hashlib.sha256(data).hexdigest()
        self.shasumFilename = os.path.join(self.artifactDir, self.shasum)

        if os.path.exists(self.shasumFilename):
            log.msg("Not storing duplicate content " + self.shasum)
            os.remove(self.fp.name)
        else:
            os.rename(self.fp.name, self.shasumFilename)
            umask = os.umask(0)
            os.umask(umask)
            os.chmod(self.shasumFilename, 0o666 & ~umask)

        return self.shasum, self.shasumFilename
