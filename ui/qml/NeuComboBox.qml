pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
ComboBox {
    id: root
    implicitHeight: 40
    implicitWidth: 126
    font.family: Theme.font
    font.pixelSize: 13
    leftPadding: 14
    rightPadding: 28
    background: Item {
        RaisedSurface { anchors.fill: parent }
        Rectangle { anchors.fill: parent; color: "transparent"; radius: Theme.controlRadius; border.width: root.activeFocus ? 1 : 0; border.color: Theme.accent }
    }
    contentItem: Text { text: root.displayText; color: Theme.text; font: root.font; verticalAlignment: Text.AlignVCenter; elide: Text.ElideRight }
    indicator: Text { x: root.width-24; anchors.verticalCenter: parent.verticalCenter; text: "⌄"; color: Theme.muted }
    delegate: ItemDelegate {
        id: choice
        required property var modelData
        required property int index
        width: root.width
        text: String(modelData)
        font: root.font
        highlighted: root.highlightedIndex === index
        contentItem: Text { text: String(choice.modelData); color: Theme.text; font: root.font; verticalAlignment: Text.AlignVCenter }
        background: Rectangle { color: choice.highlighted ? "#303030" : Theme.surface }
    }
    popup: Popup {
        y: root.height + 6
        width: root.width
        padding: 6
        implicitHeight: Math.min(contentItem.implicitHeight + 12, 300)
        background: Rectangle { color: Theme.surface; radius: Theme.smallRadius; border.color: "#353535" }
        contentItem: ListView {
            clip: true
            implicitHeight: contentHeight
            model: root.popup.visible ? root.delegateModel : null
            currentIndex: root.highlightedIndex
            ScrollIndicator.vertical: ScrollIndicator {}
        }
    }
}
