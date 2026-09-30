"""Real typed session-bus integration. CI runs under dbus-run-session."""

import json
import os
from pathlib import Path
import subprocess
import sys
import threading

import pytest
from jeepney import HeaderFields, MessageType, new_method_return, new_error
from jeepney.io.blocking import open_dbus_connection


@pytest.mark.parametrize("reply_kind", ["uint", "variant", "signed", "error"])
def test_notify_has_freedesktop_signature_and_delivery_reply(reply_kind):
    if not os.environ.get("DBUS_SESSION_BUS_ADDRESS"):
        pytest.skip("Requires a private D-Bus session; CI runs dbus-run-session")
    received = []
    errors = []
    bus = open_dbus_connection(bus="SESSION")
    assert bus.bus_proxy.RequestName("org.freedesktop.Notifications", 4) == (1,)

    def receive():
        try:
            while True:
                message = bus.receive(timeout=4)
                if message.header.message_type != MessageType.method_call:
                    continue
                received.append(message)
                if reply_kind == "error":
                    reply = new_error(
                        message, "org.freedesktop.DBus.Error.Failed", "s", ("Rejected",)
                    )
                else:
                    signature, body = {
                        "uint": ("u", (1,)),
                        "signed": ("i", (1,)),
                        "variant": ("av", ([("i", 1)],)),
                    }[reply_kind]
                    reply = new_method_return(message, signature, body)
                bus.send(reply)
                return
        except Exception as exc:
            errors.append(exc)

    thread = threading.Thread(target=receive)
    thread.start()
    try:
        process = subprocess.run(
            [
                sys.executable,
                str(Path(__file__).parents[1] / "ui" / "notification_transport.py"),
            ],
            input=json.dumps(["Calendar", "icon", "Test", "Body", 7000]),
            capture_output=True,
            text=True,
            timeout=5,
        )
        thread.join(timeout=5)
        assert not thread.is_alive()
        assert not errors
        assert (
            received
            and received[0].header.fields[HeaderFields.signature] == "susssasa{sv}i"
        ), process.stderr
        assert received[0].body[3:5] == ("Test", "Body")
        assert process.returncode == (0 if reply_kind == "uint" else 1), process.stderr
    finally:
        thread.join(timeout=5)
        bus.close()
