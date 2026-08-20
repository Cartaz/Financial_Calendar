import QtQuick
import QtQuick.Controls
import "Theme.js" as Theme

Button {
    id: control

    property bool selected: false

    implicitHeight: 38
    padding: 0
    hoverEnabled: true

    contentItem: Text {
        text: control.text
        color: control.selected
               ? Theme.accent
               : control.hovered ? Theme.text : Theme.textSecondary
        font.pixelSize: 12
        font.weight: control.selected ? Font.DemiBold : Font.Normal
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }

    background: Item {
        RaisedSurface {
            anchors.fill: parent
            visible: !control.selected
            cornerRadius: 12
            fillColor: control.hovered ? Theme.surfaceHover : Theme.surface
            shadowBlur: Theme.compactBlur
            shadowOffset: Theme.compactOffset
            shadowSpread: Theme.compactSpread
        }

        InsetSurface {
            anchors.fill: parent
            visible: control.selected
            cornerRadius: 12
            fillColor: Theme.inset
            depth: 6
            focused: control.visualFocus
        }
    }
}
