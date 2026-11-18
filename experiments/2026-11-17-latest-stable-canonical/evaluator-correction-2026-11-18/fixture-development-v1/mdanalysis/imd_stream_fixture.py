"""Deterministic local IMDv3 input fixture, using the upstream protocol server.

The context supplies a server URL and atom count. The audience still constructs
and uses the actual MDAnalysis reader. Nothing replaces the evaluated API.
"""
from contextlib import contextmanager
from threading import Thread


@contextmanager
def imd_stream(trr_path):
    """Serve one immutable TRR trajectory over a fresh loopback-only socket."""
    from MDAnalysis.coordinates.TRR import TRRReader
    from imdclient.tests.server import InThreadIMDServer
    from imdclient.tests.utils import create_default_imdsinfo_v3

    trajectory = TRRReader(trr_path)
    server = InThreadIMDServer(trajectory)
    server.set_imdsessioninfo(create_default_imdsinfo_v3())
    errors = []
    server.handshake_sequence("127.0.0.1")

    def send_rest():
        try:
            server.join_accept_thread()
            if server.conn is not None:
                server.send_frames(1, len(trajectory))
                server.disconnect()
        except (BrokenPipeError, ConnectionResetError):
            # Closing a reader before consuming the stream is a valid use.
            pass
        except Exception as error:
            errors.append(error)

    sender = Thread(target=send_rest, daemon=True)
    sender.start()
    try:
        yield {"imd_url": f"imd://127.0.0.1:{server.port}",
               "imd_n_atoms": trajectory.n_atoms}
    finally:
        server.cleanup()
        sender.join(timeout=7)
        trajectory.close()
        if sender.is_alive():
            raise RuntimeError("The controlled IMD stream did not shut down")
        if errors:
            raise RuntimeError("The controlled IMD stream failed") from errors[0]
