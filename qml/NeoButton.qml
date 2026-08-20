import QtQuick
import QtQuick.Controls
import "Theme.js" as Theme

Button {
    id: control

    implicitHeight: Theme.controlHeight
    implicitWidth: 108
    padding: 0
    hoverEnabled: true

    contentItem: Text {
        text: control.text
        color: !control.enabled
               ? Theme.disabled
               : control.hovered && !control.down
                 ? Theme.accent
                 : Theme.text
        font.pixelSize: 13
        font.weight: Font.Medium
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }

    background: Item {
        RaisedSurface {
            anchors.fill: parent
            visible: !control.down
            fillColor: control.hovered ? Theme.surfaceHover : Theme.surface
            cornerRadius: Theme.radiusMedium
            shadowBlur: Theme.controlBlur
            shadowOffset: Theme.controlOffset
            shadowSpread: Theme.controlSpread
            opacity: control.enabled ? 1 : 0.55
        }

        InsetSurface {
            anchors.fill: parent
            visible: control.down
            fillColor: Theme.surfacePressed
            cornerRadius: Theme.radiusMedium
            focused: control.visualFocus
            depth: 9
        }

        Rectangle {
            anchors.fill: parent
            radius: Theme.radiusMedium
            color: "transparent"
            border.width: control.visualFocus ? 1 : 0
            border.color: Theme.accent
        }
    }
}
