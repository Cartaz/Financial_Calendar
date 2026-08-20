import QtQuick
import QtQuick.Controls
import "Theme.js" as Theme

ScrollBar {
    id: control

    implicitWidth: orientation === Qt.Vertical ? 10 : 80
    implicitHeight: orientation === Qt.Vertical ? 80 : 10
    policy: ScrollBar.AsNeeded

    background: InsetSurface {
        visible: control.size < 1.0
        cornerRadius: 4
        fillColor: "#111111"
        depth: 4
    }

    contentItem: RaisedSurface {
        cornerRadius: 4
        fillColor: control.pressed ? "#252525" : "#202020"
        shadowBlur: 6
        shadowOffset: 1.5
        shadowSpread: 0
        lightShadow: "#302E2E2E"
        darkShadow: "#58000000"
        edgeHighlight: false
    }
}
