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
    property string errorText:
        sourceKey === "ig" ? bridge.igError : bridge.fxError

    property var visualOrder: sourceKey === "ig"
        ? [0, 1, 2, 3, 4, 5, 6, 7]
        : [0, 1, 2, 3, 4, 5, 6, 7, 8]
    property bool restoringColumns: false

    function logicalColumn(visualColumn) {
        if (visualColumn < 0 || visualColumn >= root.visualOrder.length)
            return visualColumn
        return root.visualOrder[visualColumn]
    }

    function restoreColumnOrder() {
        var desired = bridge.getColumnOrder(root.sourceKey)
        if (!desired || desired.length !== root.visualOrder.length)
            return

        var current = []
        for (var i = 0; i < root.visualOrder.length; ++i)
            current.push(i)

        root.restoringColumns = true
        for (var visual = 0; visual < desired.length; ++visual) {
            var wantedLogical = desired[visual]
            var currentVisual = current.indexOf(wantedLogical)
            if (currentVisual >= 0 && currentVisual !== visual) {
                tableView.moveColumn(currentVisual, visual)
                var moved = current.splice(currentVisual, 1)[0]
                current.splice(visual, 0, moved)
            }
        }
        root.visualOrder = current
        root.restoringColumns = false
        tableView.forceLayout()
    }

    Component.onCompleted: Qt.callLater(root.restoreColumnOrder)

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
                Layout.maximumWidth: 680
                text: root.status === "error"
                    ? "Errore aggiornamento: " + root.errorText
                      + " — ultimi dati: " + root.lastRefresh
                    : "Ultimo aggiornamento: " + root.lastRefresh
                color: root.status === "error" ? Theme.danger : Theme.textSecondary
                font.pixelSize: 11
                font.family: "monospace"
                elide: Text.ElideRight
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
                        text: {
                            var logical = root.logicalColumn(column)
                            var marker = ""
                            if (root.tableModel.sortColumnIndex === logical)
                                marker = root.tableModel.sortAscending ? "  ↑" : "  ↓"
                            return display + marker
                        }
                        color: Theme.textSecondary
                        font.pixelSize: 10
                        font.family: "monospace"
                        font.weight: Font.DemiBold
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }

                    TapHandler {
                        gesturePolicy: TapHandler.ReleaseWithinBounds
                        onTapped: bridge.sortColumn(
                            root.sourceKey,
                            root.logicalColumn(column)
                        )
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

            ItemSelectionModel {
                id: tableSelection
                model: root.tableModel
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

                selectionModel: tableSelection
                selectionBehavior: TableView.SelectRows
                selectionMode: TableView.SingleSelection
                keyNavigationEnabled: true
                pointerNavigationEnabled: true
                activeFocusOnTab: true

                columnWidthProvider: function(column) {
                    return bridge.preferredColumnWidth(
                        root.sourceKey,
                        root.logicalColumn(column)
                    )
                }

                onColumnMoved: function(logicalIndex, oldVisualIndex, newVisualIndex) {
                    var next = root.visualOrder.slice()
                    if (oldVisualIndex >= 0 && oldVisualIndex < next.length
                            && newVisualIndex >= 0 && newVisualIndex < next.length) {
                        var moved = next.splice(oldVisualIndex, 1)[0]
                        next.splice(newVisualIndex, 0, moved)
                        root.visualOrder = next
                    }
                    if (!root.restoringColumns) {
                        bridge.columnMoved(
                            root.sourceKey,
                            logicalIndex,
                            oldVisualIndex,
                            newVisualIndex
                        )
                    }
                    tableView.forceLayout()
                }

                delegate: Rectangle {
                    required property var display
                    required property var foreground
                    required property var flagUrl
                    required property int column
                    required property int row
                    required property bool selected
                    required property bool current

                    property int logicalColumnIndex: root.logicalColumn(column)

                    implicitHeight: 30
                    color: selected
                        ? "#242424"
                        : (row % 2 === 0 ? Theme.background : "#171717")
                    border.width: 1
                    border.color: current ? Theme.accent : Theme.divider

                    Row {
                        anchors.fill: parent
                        anchors.leftMargin: 9
                        anchors.rightMargin: 9
                        spacing: 6

                        Image {
                            visible: parent.parent.logicalColumnIndex === 2
                                     && flagUrl !== ""
                            width: visible ? 18 : 0
                            height: 12
                            anchors.verticalCenter: parent.verticalCenter
                            source: flagUrl
                            fillMode: Image.PreserveAspectFit
                        }

                        Text {
                            width: parent.width
                                   - (parent.parent.logicalColumnIndex === 2
                                      && flagUrl !== "" ? 24 : 0)
                            height: parent.height
                            text: display
                            color: foreground
                            font.pixelSize: 11
                            font.weight:
                                ((root.sourceKey === "ig"
                                  && parent.parent.logicalColumnIndex === 3)
                                 || (root.sourceKey !== "ig"
                                     && parent.parent.logicalColumnIndex === 4))
                                ? Font.DemiBold : Font.Normal
                            horizontalAlignment:
                                parent.parent.logicalColumnIndex === 2
                                ? Text.AlignLeft : Text.AlignHCenter
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
