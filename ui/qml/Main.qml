pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQml.Models
ApplicationWindow {
    id: root
    required property var calendar
    required property var preferences
    required property var exporter
    required property var logs
    width: 1360
    height: 820
    minimumWidth: 820
    minimumHeight: 560
    title: "Calendario Finanziario"
    color: Theme.surface
    font.family: Theme.font
    font.pixelSize: 13
    property string feedback: ""
    Shortcut { sequence: "Ctrl+R"; onActivated: root.calendar.refresh("ig") }
    Shortcut { sequence: "Ctrl+F"; onActivated: root.calendar.refresh("fxstreet") }
    Shortcut { sequence: "Ctrl+Q"; onActivated: Qt.quit() }
    Connections { target: root.calendar; function onMessage(message) { root.feedback = message; toastTimer.restart() } }
    Connections { target: root.exporter; function onMessage(message) { root.feedback = message; toastTimer.restart() } }
    Timer { id: toastTimer; interval: 8000; onTriggered: root.feedback = "" }
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 22
        spacing: 14
        RowLayout {
            Layout.fillWidth: true
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 4
                Label { text: "Calendario finanziario"; color: Theme.text; font.pixelSize: 23; font.weight: Font.DemiBold }
                Label { text: root.calendar.status; color: Theme.muted; font.pixelSize: 12 }
            }
            Item { Layout.fillWidth: true }
            NeuButton { text: "Aggiorna tutto"; emphasized: true; onClicked: root.calendar.refresh("combined") }
            NeuButton { text: "Impostazioni"; onClicked: settingsPopup.open() }
            NeuButton { text: "Log"; checkable: true; checked: logPane.visible; onClicked: logPane.visible = !logPane.visible }
        }
        ListView {
            id: sources
            Layout.fillWidth: true
            Layout.preferredHeight: 62
            orientation: ListView.Horizontal
            spacing: 14
            model: root.calendar.sourceModel
            interactive: false
            delegate: NeuButton {
                required property string key
                required property string label
                required property string status
                required property string freshness
                required property bool refreshing
                width: (sources.width - 28) / 3
                height: 62
                text: label + "  ·  " + (refreshing ? "Aggiornamento…" : freshness)
                checked: root.calendar.state.active_source === key
                enabled: !root.calendar.busy
                onClicked: root.calendar.selectSource(key)
                ToolTip.visible: hovered
                ToolTip.text: status
            }
        }
        RowLayout {
            Layout.fillWidth: true
            spacing: 12
            NeuComboBox {
                objectName: "regionFilter"
                Accessible.name: "Paese"
                model: ["ALL", "EUR", "USA", "JPN", "GBP", "CHF", "CAD", "AUD", "NZD", "CNY"]
                currentIndex: Math.max(0, model.indexOf(root.calendar.state.region))
                enabled: !root.calendar.busy
                onActivated: root.calendar.setFilter("region", currentText)
            }
            NeuComboBox {
                Accessible.name: "Impatto"
                model: ["ALL", "HIGH", "MID", "LOW"]
                currentIndex: Math.max(0, model.indexOf(root.calendar.state.impact))
                enabled: !root.calendar.busy
                onActivated: root.calendar.setFilter("impact", currentText)
            }
            NeuComboBox {
                id: range
                Accessible.name: "Intervallo"
                property var values: ["all", "today", "tomorrow", "next24", "manual"]
                model: ["Tutte le date", "Oggi", "Domani", "Prossime 24 h", "Data specifica"]
                implicitWidth: 156
                currentIndex: Math.max(0, values.indexOf(root.calendar.state.quick_range))
                enabled: !root.calendar.busy
                onActivated: { if (currentIndex === 4) settingsPopup.open(); else root.calendar.setFilter("range", values[currentIndex]) }
            }
            NeuTextField {
                id: search
                objectName: "searchField"
                Layout.fillWidth: true
                placeholderText: "Cerca evento o valore…"
                onTextEdited: searchDelay.restart()
                Timer { id: searchDelay; interval: 250; onTriggered: root.calendar.setFilter("search", search.text) }
            }
        }
        RowLayout {
            Layout.fillWidth: true
            Label { Layout.fillWidth: true; text: root.calendar.summary; color: Theme.accent; elide: Text.ElideRight }
            Label { text: root.calendar.count + " eventi"; color: Theme.muted }
            NeuButton { text: "CSV"; implicitHeight: 32; enabled: !root.exporter.busy && root.calendar.count > 0; onClicked: root.exporter.exportVisible("csv") }
            NeuButton { text: "ICS"; implicitHeight: 32; enabled: !root.exporter.busy && root.calendar.count > 0; onClicked: root.exporter.exportVisible("ics") }
        }
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumHeight: 150
            InsetSurface { anchors.fill: parent; radius: Theme.cardRadius }
            HorizontalHeaderView {
                id: header
                objectName: "eventHeader"
                anchors.top: parent.top
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.margins: 10
                height: 42
                syncView: table
                movableColumns: !root.calendar.busy
                clip: true
                delegate: Item {
                    id: headerCell
                    required property string display
                    required property int column
                    implicitHeight: 42
                    implicitWidth: 112
                    NeuButton {
                    anchors.fill: parent
                    anchors.margins: 3
                    text: headerCell.display
                    enabled: !root.calendar.busy
                    onClicked: root.calendar.sortColumn(headerCell.column)
                    Keys.onLeftPressed: event => { if (event.modifiers & Qt.AltModifier) root.calendar.moveColumn(headerCell.column, headerCell.column - 1); else event.accepted = false }
                    Keys.onRightPressed: event => { if (event.modifiers & Qt.AltModifier) root.calendar.moveColumn(headerCell.column, headerCell.column + 1); else event.accepted = false }
                    ToolTip.visible: hovered
                    ToolTip.text: "Ordina · Alt+← / Alt+→ sposta la colonna"
                    }
                }
            }
            TableView {
                id: table
                objectName: "eventsTable"
                anchors.top: header.bottom
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                anchors.margins: 10
                clip: true
                reuseItems: true
                property bool resettingOrder: false
                onColumnMoved: (logicalIndex, oldVisualIndex, newVisualIndex) => { if (!resettingOrder) root.calendar.moveColumn(oldVisualIndex, newVisualIndex) }
                Connections {
                    target: root.calendar
                    function onAccepted() {
                        table.resettingOrder = true
                        table.clearColumnReordering()
                        table.resettingOrder = false
                        table.forceLayout()
                    }
                }
                model: root.calendar.tableModel
                selectionModel: ItemSelectionModel { model: table.model }
                selectionBehavior: TableView.SelectRows
                columnWidthProvider: column => root.calendar.tableModel.columnWidth(column)
                rowHeightProvider: () => 48
                ScrollBar.vertical: ScrollBar {}
                ScrollBar.horizontal: ScrollBar {}
                delegate: Rectangle {
                    id: cell
                    required property int row
                    required property int column
                    required property string display
                    required property string columnKey
                    required property string impactLevel
                    required property string flagUrl
                    required property string timing
                    required property string duplicate
                    required property bool isPast
                    required property bool isNextHigh
                    required property bool selected
                    implicitWidth: 112
                    implicitHeight: 48
                    color: selected ? "#342418" : (row % 2 ? "#191919" : Theme.surface)
                    Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: cell.isNextHigh ? "#66502e" : "#232323" }
                    Row {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 7
                        Image { visible: cell.columnKey === "country" && cell.flagUrl !== ""; source: visible ? cell.flagUrl : ""; width: visible ? 22 : 0; height: 16; anchors.verticalCenter: parent.verticalCenter; fillMode: Image.PreserveAspectFit }
                        Column {
                            width: parent.width - (cell.columnKey === "country" ? 29 : 0)
                            anchors.verticalCenter: parent.verticalCenter
                            Text {
                                width: parent.width
                                text: cell.display
                                color: cell.columnKey === "impact" && cell.impactLevel === "HIGH" ? Theme.accent : (cell.isPast ? Theme.muted : Theme.text)
                                font.family: Theme.font
                                font.pixelSize: 12
                                elide: Text.ElideRight
                            }
                            Text { visible: cell.columnKey === "event_name" && (cell.timing !== "" || cell.duplicate !== ""); text: cell.timing + (cell.duplicate ? "  ·  corrispondenza " + cell.duplicate : ""); color: Theme.muted; font.pixelSize: 10 }
                        }
                    }
                    HoverHandler { id: cellHover }
                    ToolTip.visible: cellHover.hovered
                    ToolTip.text: cell.display
                    Accessible.name: display
                }
                Label { anchors.centerIn: parent; visible: root.calendar.count === 0; text: root.calendar.busy ? "Caricamento…" : "Nessun evento per questi filtri"; color: Theme.muted }
            }
        }
        Label { Layout.fillWidth: true; visible: text !== ""; text: root.feedback || root.calendar.error; color: root.feedback ? Theme.text : Theme.accent; elide: Text.ElideRight; ToolTip.visible: errorHover.hovered; ToolTip.text: text; HoverHandler { id: errorHover } }
        Item {
            id: logPane
            visible: false
            Layout.fillWidth: true
            Layout.preferredHeight: Math.min(160, root.height * 0.2)
            InsetSurface { anchors.fill: parent }
            NeuButton { id: copyLog; anchors.right: parent.right; anchors.top: parent.top; text: "Copia log"; onClicked: root.logs.copy() }
            ListView {
                anchors.fill: parent
                anchors.margins: 12
                anchors.rightMargin: copyLog.width + 20
                clip: true
                reuseItems: true
                model: root.logs
                delegate: Text {
                    required property string time
                    required property string level
                    required property string message
                    width: ListView.view.width
                    text: time + " [" + level + "] " + message
                    color: level === "ERROR" ? Theme.accent : Theme.muted
                    font.pixelSize: 11
                    wrapMode: Text.Wrap
                }
                ScrollBar.vertical: ScrollBar {}
            }
        }
    }
    Popup {
        id: settingsPopup
        anchors.centerIn: parent
        width: 460
        padding: 26
        modal: true
        focus: true
        onClosed: root.calendar.reload()
        background: Rectangle { color: Theme.surface; radius: Theme.panelRadius; border.color: "#363636" }
        contentItem: ColumnLayout {
            spacing: 16
            Label { text: "Impostazioni"; font.pixelSize: 22; color: Theme.text }
            Label { text: "Fuso orario · local, UTC o Europe/Rome"; color: Theme.muted }
            NeuTextField { Layout.fillWidth: true; placeholderText: "Fuso orario"; text: root.calendar.state.timezone_name || "local"; onEditingFinished: root.calendar.setFilter("timezone_name", text) }
            Label { text: "Data specifica · AAAA-MM-GG (vuoto: tutte)"; color: Theme.muted }
            NeuTextField { Layout.fillWidth: true; placeholderText: "AAAA-MM-GG"; text: root.calendar.state.date || ""; onEditingFinished: root.calendar.setFilter("selected_date", text) }
            RowLayout {
                Label { Layout.fillWidth: true; text: "Aggiornamento automatico (min)"; color: Theme.text }
                NeuComboBox { model: ["0", "5", "15", "30", "60"]; currentIndex: Math.max(0, model.indexOf(String(root.calendar.state.auto_refresh_minutes))); onActivated: root.preferences.setAutoRefresh(Number(currentText)) }
            }
            RowLayout {
                Label { Layout.fillWidth: true; text: "Anticipo notifiche HIGH (min)"; color: Theme.text }
                NeuComboBox { model: ["0", "5", "15", "30", "60"]; currentIndex: Math.max(0, model.indexOf(String(root.calendar.state.high_notification_minutes))); onActivated: root.preferences.setNotificationLead(Number(currentText)) }
            }
            Label { text: "0 disattiva · Ctrl+R ForexFactory · Ctrl+F FXStreet"; color: Theme.muted; font.pixelSize: 11 }
            NeuButton { text: "Chiudi"; Layout.alignment: Qt.AlignRight; onClicked: settingsPopup.close() }
        }
    }
}
