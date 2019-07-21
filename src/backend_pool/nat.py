from threading import Lock

from twisted.internet import reactor, protocol


class ClientProtocol(protocol.Protocol):
    def dataReceived(self, data):
        self.server_protocol.transport.write(data)

    def connectionLost(self, reason):
        self.server_protocol.transport.loseConnection()


class ClientFactory(protocol.ClientFactory):
    def __init__(self, server_protocol):
        self.server_protocol = server_protocol

    def buildProtocol(self, addr):
        client_protocol = ClientProtocol()
        client_protocol.server_protocol = self.server_protocol
        self.server_protocol.client_protocol = client_protocol
        return client_protocol


class ServerProtocol(protocol.Protocol):
    def __init__(self, dst_ip, dst_port):
        self.dst_ip = dst_ip
        self.dst_port = dst_port
        self.client_protocol = None
        self.buffer = []

    def connectionMade(self):
        reactor.connectTCP(self.dst_ip, self.dst_port, ClientFactory(self))

    def dataReceived(self, data):
        self.buffer.append(data)
        self.sendData()

    def sendData(self):
        if not self.client_protocol:
            reactor.callLater(0.5, self.sendData)
            return

        for packet in self.buffer:
            self.client_protocol.transport.write(packet)
        self.buffer = []

    def connectionLost(self, reason):
        if self.client_protocol:
            self.client_protocol.transport.loseConnection()


class ServerFactory(protocol.Factory):
    def __init__(self, dst_ip, dst_port):
        self.dst_ip = dst_ip
        self.dst_port = dst_port

    def buildProtocol(self, addr):
        return ServerProtocol(self.dst_ip, self.dst_port)


class NATService:
    def __init__(self):
        self.bindings = {}
        self.lock = Lock()  # we need to be thread-safe just in case, this is accessed from multiple clients

    def request_binding(self, guest_id, dst_ip, ssh_port, telnet_port):
        self.lock.acquire()
        try:
            # see if binding is already created
            if dst_ip in self.bindings:
                # increase connected
                self.bindings[guest_id][0] += 1

                return self.bindings[guest_id][1]._realPortNumber, self.bindings[guest_id][2]._realPortNumber

            else:
                nat_ssh = reactor.listenTCP(0, ServerFactory(dst_ip, ssh_port), interface='0.0.0.0')
                nat_telnet = reactor.listenTCP(0, ServerFactory(dst_ip, telnet_port), interface='0.0.0.0')
                self.bindings[guest_id] = [0, nat_ssh, nat_telnet]

                return nat_ssh._realPortNumber, nat_telnet._realPortNumber
        finally:
            self.lock.release()

    def free_binding(self, guest_id):
        self.lock.acquire()
        try:
            self.bindings[guest_id][0] -= 1

            # stop listening if no-one connected
            if self.bindings[guest_id][0] == 0:
                self.bindings[guest_id][1].stopListening()
                self.bindings[guest_id][2].stopListening()

        finally:
            self.lock.release()
