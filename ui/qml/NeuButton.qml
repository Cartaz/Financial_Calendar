import QtQuick
import QtQuick.Controls
Button {
    id: root
    property bool emphasized: false
    implicitHeight: 40
    implicitWidth: Math.max(78, contentItem.implicitWidth + 28)
    padding: 12
    font.family: Theme.font
    font.pixelSize: 13
    hoverEnabled: true
    opacity: enabled ? 1 : 0.4
    Accessible.name: text
    background: Item {
        RaisedSurface { anchors.fill: parent; visible: !root.down && !root.checked; fill: root.hovered ? "#1c1c1c" : Theme.surface }
        InsetSurface { anchors.fill: parent; visible: root.down || root.checked }
        Rectangle { anchors.fill: parent; radius: Theme.controlRadius; color: "transparent"; border.color: Theme.accent; border.width: root.activeFocus ? 1 : 0 }
    }
    contentItem: Text {
        text: root.text
        color: root.checked || root.emphasized ? Theme.accent : Theme.text
        font: root.font
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }
    Behavior on opacity { NumberAnimation { duration: Theme.duration } }
}
