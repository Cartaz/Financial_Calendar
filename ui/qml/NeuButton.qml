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
    background: NeuControlSurface {
        pressed: root.down
        selected: root.checked
        hovered: root.hovered
        focused: root.activeFocus
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
