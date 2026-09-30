import QtQuick
import QtQuick.Effects
Item {
    id: root
    property real radius: Theme.controlRadius
    property color fill: Theme.surface
    property bool hovered: false
    property bool strong: false
    RectangularShadow {
        anchors.fill: plate
        offset: root.strong ? Theme.strongDarkOffset : (root.hovered ? Theme.hoverDarkOffset : Theme.softDarkOffset)
        radius: root.radius
        blur: root.strong ? Theme.strongDarkBlur : (root.hovered ? Theme.hoverDarkBlur : Theme.softDarkBlur)
        spread: 0
        color: root.strong ? Theme.strongDarkShadow : Theme.softDarkShadow
        cached: false
    }
    RectangularShadow {
        anchors.fill: plate
        offset: root.strong ? Theme.strongLightOffset : (root.hovered ? Theme.hoverLightOffset : Theme.softLightOffset)
        radius: root.radius
        blur: root.strong ? Theme.strongLightBlur : (root.hovered ? Theme.hoverLightBlur : Theme.softLightBlur)
        spread: 0
        color: root.strong ? Theme.strongLightShadow : Theme.softLightShadow
        cached: false
    }
    Rectangle { id: plate; anchors.fill: parent; color: root.fill; radius: root.radius; border.color: Theme.divider }
}
