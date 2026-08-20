import QtQuick
import QtQuick.Controls
import "Theme.js" as Theme

CheckBox {
    id: control
    spacing: 9

    indicator: Item {
        implicitWidth: 18
        implicitHeight: 18
        x: 0
        y: (control.height - height) / 2

        InsetSurface {
            anchors.fill: parent
            visible: !control.checked
            cornerRadius: 5
            focused: control.visualFocus
            fillColor: Theme.inset
            depth: 5
        }

        RaisedSurface {
            anchors.fill: parent
            visible: control.checked
            cornerRadius: 5
            fillColor: Theme.accent
            shadowBlur: 5
            shadowOffset: 2
            shadowSpread: -1
            lightShadow: Theme.shadowLight
            darkShadow: Theme.shadowDark
            edgeHighlight: false
        }

        Text {
            anchors.centerIn: parent
            visible: control.checked
            text: "✓"
            color: "#111111"
            font.pixelSize: 12
            font.bold: true
        }
    }

    contentItem: Text {
        text: control.text
        color: control.enabled ? Theme.textSecondary : Theme.disabled
        font.pixelSize: 12
        verticalAlignment: Text.AlignVCenter
        leftPadding: control.indicator.width + control.spacing
    }
}
