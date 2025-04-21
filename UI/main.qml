import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

ApplicationWindow {
    visible: true
    width: 600
    height: 600
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
                ListElement { name: "Profit Calculation"; idNum: 2 }
                ListElement { name: "Shop Management"; idNum: 3 }
                ListElement { name: "Collusion Detection"; idNum: 4 }
                ListElement { name: "Fraud Detection"; idNum: 5 }
                ListElement { name: "Historical Data Management"; idNum: 6 }
            }

            delegate: Rectangle {
                id: buttonRect
                color: "#006d5b"
                radius: 10
                border.color: hoverArea.containsMouse ? "#004d40" : "white"
                border.width: hoverArea.containsMouse ? 4 : 2
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.preferredWidth: 1
                Layout.preferredHeight: 1

                Text {
                    text: model.name
                    anchors.fill: parent
                    anchors.margins: 10
                    color: "white"
                    font.pixelSize: 18
                    wrapMode: Text.Wrap // <-- Satır kaydırması AKTİF
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    maximumLineCount: 4 // İstersen maksimum 4 satırda sınırla
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
