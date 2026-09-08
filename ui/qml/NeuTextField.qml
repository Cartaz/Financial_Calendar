import QtQuick
import QtQuick.Controls
TextField {
    id: root
    implicitHeight: 40
    leftPadding: 14
    rightPadding: 14
    color: Theme.text
    placeholderTextColor: Theme.muted
    selectionColor: Theme.accent
    selectedTextColor: Theme.surface
    font.family: Theme.font
    font.pixelSize: 13
    Accessible.name: placeholderText
    background: Item {
        InsetSurface { anchors.fill: parent }
        Rectangle { anchors.fill: parent; color: "transparent"; radius: Theme.controlRadius; border.width: root.activeFocus ? 1 : 0; border.color: Theme.accent }
    }
}
