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
}
