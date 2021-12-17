# Copyright (c) 2018 Michel Oosterhof
# See LICENSE for details.
from __future__ import annotations

import os
import unittest

from cowrie.shell import protocol
from cowrie.test import fake_server, fake_transport

os.environ["COWRIE_HONEYPOT_DATA_PATH"] = "data"
os.environ["COWRIE_HONEYPOT_DOWNLOAD_PATH"] = "/tmp"
os.environ["COWRIE_SHELL_FILESYSTEM"] = "share/cowrie/fs.pickle"

PROMPT = b"root@unitTest:~# "


class ShellTftpCommandTests(unittest.TestCase):
    """Tests for cowrie/commands/tftp.py."""

    def setUp(self) -> None:
        self.proto = protocol.HoneyPotInteractiveProtocol(
            fake_server.FakeAvatar(fake_server.FakeServer())
        )
        self.tr = fake_transport.FakeTransport("1.1.1.1", "1111")
        self.proto.makeConnection(self.tr)
        self.tr.clear()

    def tearDown(self) -> None:
        self.proto.connectionLost("tearDown From Unit Test")

    def test_echo_command_001(self) -> None:
        self.proto.lineReceived(b"tftp\n")
        self.assertEqual(
            self.tr.value(),
            b"usage: tftp [-h] [-c C C] [-l L] [-g G] [-p P] [-r R] [hostname]\n" + PROMPT,
        )
