pragma Singleton
import QtQuick
QtObject {
    readonly property color surface: "#141414"
    readonly property color accent: "#ff6600"
    readonly property color text: Qt.rgba(225/255,225/255,225/255,1)
    readonly property color muted: Qt.rgba(135/255,135/255,135/255,1)
    readonly property color subdued: Qt.rgba(90/255,90/255,90/255,1)
    readonly property string font: "Noto Sans"
    readonly property int panelRadius: 28
    readonly property int cardRadius: 22
    readonly property int controlRadius: 16
    readonly property int smallRadius: 12
    readonly property int duration: 120
    readonly property color divider: "#232323"
    readonly property color insetDark: "#090909"
    readonly property color insetLight: "#1e1e1e"
    readonly property vector2d strongDarkOffset: Qt.vector2d(8, 8)
    readonly property vector2d strongLightOffset: Qt.vector2d(-6, -6)
    readonly property vector2d softDarkOffset: Qt.vector2d(3.5, 3.5)
    readonly property vector2d softLightOffset: Qt.vector2d(-3, -3)
    readonly property vector2d hoverDarkOffset: Qt.vector2d(4.5, 4.5)
    readonly property vector2d hoverLightOffset: Qt.vector2d(-3.8, -3.8)
    readonly property real strongDarkBlur: 20
    readonly property real strongLightBlur: 15
    readonly property real softDarkBlur: 10
    readonly property real softLightBlur: 8.5
    readonly property real hoverDarkBlur: 12
    readonly property real hoverLightBlur: 10
    readonly property color strongDarkShadow: Qt.rgba(0, 0, 0, 0.62)
    readonly property color strongLightShadow: Qt.rgba(1, 1, 1, 0.10)
    readonly property color softDarkShadow: Qt.rgba(0, 0, 0, 0.46)
    readonly property color softLightShadow: Qt.rgba(1, 1, 1, 0.075)
}
