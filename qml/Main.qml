import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "Theme.js" as Theme

ApplicationWindow {
    id: root
    visible: true
    width: 1300
    height: 800
    minimumWidth: 1100
    minimumHeight: 700
    title: "Calendario Finanziario"
    color: Theme.background

    property int activeTab: 0

    Shortcut {
        sequence: "Ctrl+Q"
        onActivated: Qt.quit()
    }

    Shortcut {
        sequence: "Ctrl+M"
        onActivated: root.hide()
    }

    Shortcut {
        sequence: "Ctrl+R"
        enabled: root.activeTab === 0
        onActivated: bridge.refresh("ig")
    }

    Shortcut {
        sequence: "Ctrl+F"
        enabled: root.activeTab === 1
        onActivated: bridge.refresh("fxstreet")
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 12

        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 42
            spacing: 12

            Text {
                text: "FUSO ORARIO"
                color: Theme.textMuted
                font.pixelSize: 10
                font.family: "monospace"
                font.letterSpacing: 1.2
            }

            NeoComboBox {
                id: timezone
                implicitWidth: 276
                model: bridge.timezoneOptions
                currentIndex: bridge.timezoneIndex
                onActivated: bridge.setTimezoneIndex(currentIndex)
            }

            Text {
                text: bridge.timezoneInfo
                color: Theme.textSecondary
                font.pixelSize: 10
                font.family: "monospace"
            }

            Item { Layout.fillWidth: true }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 38
            spacing: 7

            NeoTabButton {
                id: igTab
                text: "IG Economic Calendar"
                selected: root.activeTab === 0
                implicitWidth: 186
                onClicked: root.activeTab = 0
            }

            NeoTabButton {
                id: fxTab
                text: "FXStreet Economic Calendar"
                selected: root.activeTab === 1
                implicitWidth: 224
                onClicked: root.activeTab = 1
            }

            Item { Layout.fillWidth: true }
        }

        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: root.activeTab

            CalendarPage {
                sourceKey: "ig"
            }

            CalendarPage {
                sourceKey: "fxstreet"
            }
        }
    }

    Connections {
        target: bridge
        function onErrorMessage(message) {
            console.warn("Calendar refresh error:", message)
        }
    }
}
