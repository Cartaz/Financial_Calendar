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
    background: NeuControlSurface {
        pressed: root.down
        hovered: root.hovered
        focused: root.activeFocus
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
        contentItem: Text { text: String(choice.modelData); color: choice.highlighted ? Theme.accent : Theme.text; font: root.font; verticalAlignment: Text.AlignVCenter }
        background: Item { }
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
            highlight: InsetSurface { }
            ScrollIndicator.vertical: ScrollIndicator {}
        }
    }
}
