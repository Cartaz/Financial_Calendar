import QtQuick
Item {
    id: root
    property real radius: Theme.controlRadius
    Rectangle { anchors.fill: parent; radius: root.radius; color: "#090909" }
    Rectangle { anchors.fill: parent; anchors.topMargin: 2; anchors.leftMargin: 2; radius: root.radius - 1; color: "#1e1e1e" }
    Rectangle { anchors.fill: parent; anchors.margins: 1; anchors.topMargin: 3; anchors.leftMargin: 3; radius: root.radius - 2; color: Theme.surface }
}
