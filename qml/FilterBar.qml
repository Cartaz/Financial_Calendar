import QtQuick
import QtQuick.Layouts
import "Theme.js" as Theme

RaisedSurface {
    id: root

    property string sourceKey: "ig"
    signal filtersChanged(int regionIndex, int impactIndex,
                          bool dateEnabled, string dateText)

    height: Theme.filterHeight
    cornerRadius: Theme.radiusLarge
    shadowBlur: Theme.panelBlur
    shadowOffset: Theme.panelOffset
    shadowSpread: Theme.panelSpread
    fillColor: Theme.surface

    function emitFilters() {
        filtersChanged(region.currentIndex,
                       impact.currentIndex,
                       dateCheck.checked,
                       dateField.formatDate(dateField.selectedDate))
    }

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 18
        anchors.rightMargin: 18
        spacing: 14

        NeoCheckBox {
            id: dateCheck
            text: "Filtra per data:"
            onToggled: root.emitFilters()
        }

        DateField {
            id: dateField
            enabledField: dateCheck.checked
            onDateSelected: root.emitFilters()
        }

        Item { width: 12 }

        Text {
            text: "Regione:"
            color: Theme.textSecondary
            font.pixelSize: 12
        }

        NeoComboBox {
            id: region
            model: bridge.regionOptions
            implicitWidth: 145
            onCurrentIndexChanged: root.emitFilters()
        }

        Item { width: 12 }

        Text {
            text: "Impatto:"
            color: Theme.textSecondary
            font.pixelSize: 12
        }

        NeoComboBox {
            id: impact
            model: bridge.impactOptions
            implicitWidth: 145
            onCurrentIndexChanged: root.emitFilters()
        }

        Item { Layout.fillWidth: true }
    }
}
