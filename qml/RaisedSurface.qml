import QtQuick
import QtQuick.Effects
import "Theme.js" as Theme

Item {
    id: root

    property color fillColor: Theme.surface
    property real cornerRadius: Theme.radiusMedium
    property real shadowBlur: Theme.controlBlur
    property real shadowOffset: Theme.controlOffset
    property real shadowSpread: Theme.controlSpread
    property color lightShadow: Theme.shadowLight
    property color darkShadow: Theme.shadowDark
    property bool edgeHighlight: false

    property alias contentItem: content
    default property alias contentData: content.data

    RectangularShadow {
        anchors.fill: face
        offset: Qt.vector2d(-root.shadowOffset, -root.shadowOffset)
        blur: root.shadowBlur
        spread: root.shadowSpread
        radius: root.cornerRadius
        color: root.lightShadow
        cached: true
        antialiasing: true
    }

    RectangularShadow {
        anchors.fill: face
        offset: Qt.vector2d(root.shadowOffset, root.shadowOffset)
        blur: root.shadowBlur
        spread: root.shadowSpread
        radius: root.cornerRadius
        color: root.darkShadow
        cached: true
        antialiasing: true
    }

    Rectangle {
        id: face
        anchors.fill: parent
        radius: root.cornerRadius
        color: root.fillColor
        antialiasing: true
    }

    Item {
        id: content
        anchors.fill: parent
    }
}
