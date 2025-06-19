import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

ApplicationWindow {
    id: mainMenuWindow
    visible: true
    width: 1000
    height: 800
    title: "Main Menu"
    color: "#003333"

    GridLayout {
        anchors.fill: parent
        columns: 3
        rowSpacing: 10
        columnSpacing: 10
        anchors.margins: 20

        Repeater {
            model: ListModel {
                ListElement { name: "Dynamic Product Handling"; idNum: 1 }
                ListElement { name: "General Stats"; idNum: 2 }
                ListElement { name: "Collusion Detection With ML"; idNum: 3 }
                ListElement { name: "Collusion Detection"; idNum: 4 }
                ListElement { name: "Fraud Detection"; idNum: 5 }
                ListElement { name: "Historical Data Management"; idNum: 6 }
            }

            delegate: Rectangle {
                color: "#006d5b"
                radius: 10
                Layout.fillWidth: true
                Layout.fillHeight: true
                border.color: hoverArea.containsMouse ? "#004d40" : "white"
                border.width: hoverArea.containsMouse ? 4 : 2

                Text {
                    text: model.name
                    anchors.fill: parent
                    anchors.margins: 10
                    color: "white"
                    font.pixelSize: 18
                    wrapMode: Text.Wrap
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    maximumLineCount: 4
                }

                MouseArea {
                    id: hoverArea
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: backend.selectFeature(model.idNum)
                }
            }
        }
    }
}
