import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "Theme.js" as Theme

Control {
    id: root

    property date selectedDate: new Date()
    property bool enabledField: true
    signal dateSelected(string formattedDate)

    implicitWidth: 138
    implicitHeight: Theme.controlHeight

    function two(n) { return n < 10 ? "0" + n : "" + n }
    function formatDate(d) {
        return two(d.getDate()) + "/" + two(d.getMonth() + 1) + "/" + d.getFullYear()
    }

    contentItem: Text {
        text: root.formatDate(root.selectedDate)
        color: root.enabledField ? Theme.text : Theme.disabled
        font.pixelSize: 12
        leftPadding: 16
        verticalAlignment: Text.AlignVCenter
    }

    background: InsetSurface {
        cornerRadius: Theme.radiusMedium
        fillColor: Theme.inset
        enabledSurface: root.enabledField
        depth: 7
    }

    MouseArea {
        anchors.fill: parent
        enabled: root.enabledField
        cursorShape: Qt.PointingHandCursor
        onClicked: picker.open()
    }

    Popup {
        id: picker
        y: root.height + 6
        width: 286
        height: 300
        padding: 12

        property date shownMonth: new Date(root.selectedDate.getFullYear(),
                                           root.selectedDate.getMonth(), 1)

        background: RaisedSurface {
            cornerRadius: 16
            shadowBlur: 10
            shadowOffset: 3
            shadowSpread: -1
            fillColor: Theme.elevated
        }

        contentItem: ColumnLayout {
            spacing: 8

            RowLayout {
                Layout.fillWidth: true

                NeoButton {
                    text: "‹"
                    implicitWidth: 36
                    onClicked: picker.shownMonth =
                        new Date(picker.shownMonth.getFullYear(),
                                 picker.shownMonth.getMonth() - 1, 1)
                }

                Text {
                    Layout.fillWidth: true
                    text: picker.shownMonth.toLocaleDateString(Qt.locale("it_IT"),
                                                                "MMMM yyyy")
                    color: Theme.text
                    font.pixelSize: 13
                    font.weight: Font.Medium
                    horizontalAlignment: Text.AlignHCenter
                }

                NeoButton {
                    text: "›"
                    implicitWidth: 36
                    onClicked: picker.shownMonth =
                        new Date(picker.shownMonth.getFullYear(),
                                 picker.shownMonth.getMonth() + 1, 1)
                }
            }

            DayOfWeekRow {
                Layout.fillWidth: true
                locale: Qt.locale("it_IT")
                delegate: Text {
                    required property var model
                    text: model.shortName
                    color: Theme.textMuted
                    font.pixelSize: 10
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
            }

            MonthGrid {
                Layout.fillWidth: true
                Layout.fillHeight: true
                month: picker.shownMonth.getMonth()
                year: picker.shownMonth.getFullYear()
                locale: Qt.locale("it_IT")

                delegate: Rectangle {
                    required property var model
                    radius: 8
                    color: model.today ? "#242424" : "transparent"

                    Text {
                        anchors.centerIn: parent
                        text: model.day
                        color: model.month === picker.shownMonth.getMonth()
                               ? Theme.text : Theme.textMuted
                        font.pixelSize: 11
                    }
                }

                onClicked: function(date) {
                    root.selectedDate = date
                    root.dateSelected(root.formatDate(date))
                    picker.close()
                }
            }
        }
    }
}
