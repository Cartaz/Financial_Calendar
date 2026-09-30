import QtQuick
import QtQuick.Controls
HorizontalHeaderViewDelegate {
    id: root
    implicitHeight: 42
    implicitWidth: 112
    padding: 8
    font.family: Theme.font
    font.pixelSize: 13
    hoverEnabled: true
    opacity: enabled ? 1 : 0.4
    Accessible.name: text
    background: NeuControlSurface {
        anchors.fill: parent
        anchors.margins: 3
        pressed: root.down
        focused: root.activeFocus
        hovered: root.hovered
    }
    contentItem: Text {
        text: root.text
        color: root.activeFocus ? Theme.accent : Theme.text
        font: root.font
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }
}
