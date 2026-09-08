import QtQuick
import QtQuick.Effects
Item {
    id: root
    property real radius: Theme.controlRadius
    property color fill: Theme.surface
    RectangularShadow {
        anchors.fill: plate
        offset: Qt.vector2d(4, 4)
        radius: root.radius
        blur: 12
        spread: 0
        color: "#b0000000"
        cached: false
    }
    RectangularShadow {
        anchors.fill: plate
        offset: Qt.vector2d(-3, -3)
        radius: root.radius
        blur: 10
        spread: 0
        color: "#182f2f2f"
        cached: false
    }
    Rectangle { id: plate; anchors.fill: parent; color: root.fill; radius: root.radius; border.color: "#232323" }
}
