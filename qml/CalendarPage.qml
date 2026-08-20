import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "Theme.js" as Theme

Item {
    id: root

    property string sourceKey: "ig"
    property var tableModel: sourceKey === "ig" ? bridge.igModel : bridge.fxModel
    property string status: sourceKey === "ig" ? bridge.igStatus : bridge.fxStatus
    property string lastRefresh:
        sourceKey === "ig" ? bridge.igLastRefresh : bridge.fxLastRefresh

    ColumnLayout {
        anchors.fill: parent
        spacing: 13

        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 42
            spacing: 11

            StatusDot { state: root.status }

            NeoButton {
                text: "Aggiorna"
                enabled: root.status !== "running"
                implicitWidth: 104
                onClicked: bridge.refresh(root.sourceKey)
            }

            RaisedSurface {
                Layout.preferredWidth: 58
                Layout.preferredHeight: 34
                cornerRadius: 10
                shadowBlur: Theme.compactBlur
                shadowOffset: Theme.compactOffset
                shadowSpread: Theme.compactSpread
                fillColor: Theme.surface

                Text {
                    anchors.centerIn: parent
                    text: root.sourceKey === "ig" ? "Ctrl+R" : "Ctrl+F"
                    color: Theme.textSecondary
                    font.pixelSize: 10
                    font.family: "monospace"
                }
            }

            StatusDot { state: root.status }

            Text {
                text: "Ultimo aggiornamento: " + root.lastRefresh
                color: Theme.textSecondary
                font.pixelSize: 11
                font.family: "monospace"
            }

            Item { Layout.fillWidth: true }
        }

        FilterBar {
            Layout.fillWidth: true
            Layout.preferredHeight: Theme.filterHeight
            sourceKey: root.sourceKey
            onFiltersChanged: function(regionIndex, impactIndex,
                                        dateEnabled, dateText) {
                bridge.setFilters(root.sourceKey, regionIndex, impactIndex,
                                  dateEnabled, dateText)
            }
        }

        Item {
            id: tableFrame
            Layout.fillWidth: true
            Layout.fillHeight: true

            InsetSurface {
                anchors.fill: parent
                cornerRadius: 14
                fillColor: Theme.inset
                depth: 7
            }

            HorizontalHeaderView {
                id: header
                anchors.left: verticalHeader.right
                anchors.right: parent.right
                anchors.top: parent.top
                height: 38
                syncView: tableView
                clip: true
                movableColumns: true

                delegate: Rectangle {
                    required property var display
                    required property int column

                    implicitWidth: 120
                    implicitHeight: 38
                    color: Theme.surface
                    border.width: 1
                    border.color: Theme.divider

                    Rectangle {
                        x: 8
                        y: 1
                        width: parent.width - 16
                        height: 1
                        color: "#242424"
                    }

                    Text {
                        anchors.fill: parent
                        anchors.leftMargin: 8
                        anchors.rightMargin: 8
                        text: display
                        color: Theme.textSecondary
                        font.pixelSize: 10
                        font.family: "monospace"
                        font.weight: Font.DemiBold
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }

                    TapHandler {
                        gesturePolicy: TapHandler.ReleaseWithinBounds
                        onTapped: bridge.sortColumn(root.sourceKey, column)
                    }
                }
            }

            VerticalHeaderView {
                id: verticalHeader
                anchors.left: parent.left
                anchors.top: header.bottom
                anchors.bottom: parent.bottom
                width: 45
                syncView: tableView
                clip: true

                delegate: Rectangle {
                    required property var display
                    implicitWidth: 45
                    implicitHeight: 30
                    color: Theme.background
                    border.width: 1
                    border.color: Theme.divider
                    Text {
                        anchors.centerIn: parent
                        text: display
                        color: Theme.textSecondary
                        font.pixelSize: 10
                        font.family: "monospace"
                    }
                }
            }

            TableView {
                id: tableView
                anchors.left: verticalHeader.right
                anchors.right: parent.right
                anchors.top: header.bottom
                anchors.bottom: parent.bottom
                clip: true
                model: root.tableModel
                rowSpacing: 1
                columnSpacing: 1
                reuseItems: true

                columnWidthProvider: function(column) {
                    var widths = root.sourceKey === "ig"
                        ? [100, 66, 82, 108, 300, 90, 104, 104]
                        : [100, 66, 82, 290, 92, 90, 82, 104, 104]
                    return widths[column] || 100
                }

                delegate: Rectangle {
                    required property var display
                    required property var foreground
                    required property var flagUrl
                    required property int column
                    required property int row

                    implicitHeight: 30
                    color: row % 2 === 0 ? Theme.background : "#171717"
                    border.width: 1
                    border.color: Theme.divider

                    Row {
                        anchors.fill: parent
                        anchors.leftMargin: 9
                        anchors.rightMargin: 9
                        spacing: 6

                        Image {
                            visible: column === 2 && flagUrl !== ""
                            width: visible ? 18 : 0
                            height: 12
                            anchors.verticalCenter: parent.verticalCenter
                            source: flagUrl
                            fillMode: Image.PreserveAspectFit
                        }

                        Text {
                            width: parent.width - (column === 2 && flagUrl !== "" ? 24 : 0)
                            height: parent.height
                            text: display
                            color: foreground
                            font.pixelSize: 11
                            font.weight:
                                ((root.sourceKey === "ig" && column === 3)
                                 || (root.sourceKey !== "ig" && column === 4))
                                ? Font.DemiBold : Font.Normal
                            horizontalAlignment: column === 2
                                                 ? Text.AlignLeft
                                                 : Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                            elide: Text.ElideRight
                        }
                    }
                }

                ScrollBar.vertical: NeoScrollBar {
                    width: 10
                }

                ScrollBar.horizontal: NeoScrollBar {
                    height: 10
                }
            }
        }
    }
}
