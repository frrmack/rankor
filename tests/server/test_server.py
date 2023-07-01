from rankor.server import RankorServerThread


def test_server_start_stop():
    server = RankorServerThread()
    server.start()  
    assert server.is_alive()
    server.stop()
    assert not server.is_alive()

