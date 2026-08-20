import QtQuick
import "Theme.js" as Theme

Item {
    id: root

    property color fillColor: Theme.inset
    property real cornerRadius: Theme.radiusMedium
    property bool focused: false
    property bool enabledSurface: true
    property real depth: Theme.innerDepth

    property alias contentItem: content
    default property alias contentData: content.data

    Rectangle {
        anchors.fill: parent
        radius: root.cornerRadius
        color: root.fillColor
        border.width: root.focused ? 1 : 0
        border.color: Theme.accent
        antialiasing: true
        opacity: root.enabledSurface ? 1.0 : 0.62
    }

    Rectangle {
        x: root.cornerRadius * 0.65
        y: 0
        width: Math.max(0, root.width - root.cornerRadius * 1.3)
        height: root.depth
        opacity: root.enabledSurface ? 0.92 : 0.45
        gradient: Gradient {
            GradientStop { position: 0.00; color: "#7A000000" }
            GradientStop { position: 0.35; color: "#3A000000" }
            GradientStop { position: 1.00; color: "#00000000" }
        }
    }

    Rectangle {
        x: 0
        y: root.cornerRadius * 0.65
        width: root.depth
        height: Math.max(0, root.height - root.cornerRadius * 1.3)
        opacity: root.enabledSurface ? 0.92 : 0.45
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.00; color: "#72000000" }
            GradientStop { position: 0.35; color: "#34000000" }
            GradientStop { position: 1.00; color: "#00000000" }
        }
    }

    Rectangle {
        x: root.cornerRadius * 0.65
        y: root.height - root.depth
        width: Math.max(0, root.width - root.cornerRadius * 1.3)
        height: root.depth
        opacity: root.enabledSurface ? 0.72 : 0.32
        gradient: Gradient {
            GradientStop { position: 0.00; color: "#002C2C2C" }
            GradientStop { position: 0.65; color: "#1C2C2C2C" }
            GradientStop { position: 1.00; color: "#442C2C2C" }
        }
    }

    Rectangle {
        x: root.width - root.depth
        y: root.cornerRadius * 0.65
        width: root.depth
        height: Math.max(0, root.height - root.cornerRadius * 1.3)
        opacity: root.enabledSurface ? 0.68 : 0.30
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.00; color: "#002C2C2C" }
            GradientStop { position: 0.65; color: "#182C2C2C" }
            GradientStop { position: 1.00; color: "#3C2C2C2C" }
        }
    }

    Item {
        id: content
        anchors.fill: parent
    }
}
