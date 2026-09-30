import QtQuick
Item {
    id: root
    property bool pressed: false
    property bool selected: false
    property bool focused: false
    property bool hovered: false
    RaisedSurface { anchors.fill: parent; visible: !root.pressed && !root.selected; hovered: root.hovered }
    InsetSurface { anchors.fill: parent; visible: root.pressed || root.selected }
    Rectangle { anchors.fill: parent; radius: Theme.controlRadius; color: "transparent"; border.color: Theme.accent; border.width: root.focused ? 1 : 0 }
}
