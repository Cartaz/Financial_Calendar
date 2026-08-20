import QtQuick
import "Theme.js" as Theme

Item {
    id: root
    property string state: "stopped"
    width: 11
    height: 11

    Rectangle {
        anchors.fill: parent
        radius: width / 2
        color: root.state === "running" ? Theme.accent
             : root.state === "error" ? Theme.danger
             : Theme.textMuted
    }

    SequentialAnimation on opacity {
        running: root.state === "running"
        loops: Animation.Infinite
        NumberAnimation { from: 1; to: 0.45; duration: 520 }
        NumberAnimation { from: 0.45; to: 1; duration: 520 }
    }
}
