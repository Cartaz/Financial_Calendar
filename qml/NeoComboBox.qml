import QtQuick
import QtQuick.Controls
import "Theme.js" as Theme

ComboBox {
    id: control

    implicitHeight: Theme.controlHeight
    implicitWidth: 150
    leftPadding: 16
    rightPadding: 34
    hoverEnabled: true

    contentItem: Text {
        leftPadding: control.leftPadding
        rightPadding: control.rightPadding
        text: control.displayText
        color: control.enabled ? Theme.text : Theme.disabled
        font.pixelSize: 12
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }

    indicator: Canvas {
        x: control.width - 23
        y: control.height / 2 - 3
        width: 9
        height: 5
        contextType: "2d"

        onPaint: {
            context.reset()
            context.moveTo(0, 0)
            context.lineTo(width, 0)
            context.lineTo(width / 2, height)
            context.closePath()
            context.fillStyle = control.hovered ? Theme.accent : Theme.textSecondary
            context.fill()
        }
    }

    background: InsetSurface {
        focused: control.activeFocus
        enabledSurface: control.enabled
        cornerRadius: Theme.radiusMedium
        fillColor: Theme.inset
        depth: 7
    }

    delegate: ItemDelegate {
        required property int index

        width: control.width
        height: 34
        text: modelData
        highlighted: control.highlightedIndex === index

        contentItem: Text {
            text: parent.text
            color: parent.highlighted ? Theme.accent : Theme.text
            font.pixelSize: 12
            verticalAlignment: Text.AlignVCenter
            leftPadding: 12
        }

        background: Rectangle {
            radius: 8
            color: parent.highlighted ? "#252525" : "transparent"
        }
    }

    popup: Popup {
        y: control.height + 5
        width: control.width
        implicitHeight: Math.min(contentItem.implicitHeight + 12, 330)
        padding: 6

        contentItem: ListView {
            implicitHeight: contentHeight
            clip: true
            model: control.popup.visible ? control.delegateModel : null
            currentIndex: control.highlightedIndex
            ScrollIndicator.vertical: ScrollIndicator {}
        }

        background: RaisedSurface {
            cornerRadius: 12
            shadowBlur: 9
            shadowOffset: 3
            shadowSpread: -1
            fillColor: Theme.elevated
        }
    }
}
