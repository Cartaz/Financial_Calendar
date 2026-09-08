"""Typed Freedesktop D-Bus call isolated by a five-second parent deadline."""

import json
import sys
from jeepney import DBusAddress, MessageType, new_method_call
from jeepney.io.blocking import open_dbus_connection


def main():
    name, icon, title, body, timeout = json.load(sys.stdin)
    address = DBusAddress(
        "/org/freedesktop/Notifications",
        bus_name="org.freedesktop.Notifications",
        interface="org.freedesktop.Notifications",
    )
    # Explicit wire types work with daemons without Qt introspection annotations.
    message = new_method_call(
        address,
        "Notify",
        "susssasa{sv}i",
        (name, 0, icon, title, body, [], {}, timeout),
    )
    connection = open_dbus_connection(bus="SESSION")
    try:
        reply = connection.send_and_get_reply(message, timeout=3)
        if reply.header.message_type == MessageType.error:
            raise RuntimeError(str(reply.body))
        if not reply.body or type(reply.body[0]) is not int:
            raise RuntimeError("Risposta di consegna D-Bus non valida")
    finally:
        connection.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
