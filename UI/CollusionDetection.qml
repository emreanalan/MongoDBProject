import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

ApplicationWindow {
    id: collusionDetectionWindow
    visible: true
    width: 1000
    height: 700
    title: "Collusion Detection"
    color: "#003333"

    ColumnLayout {
        anchors.fill: parent
        spacing: 10
        anchors.margins: 20

        // Üstte tarih inputları ve buton
        RowLayout {
            spacing: 10
            Layout.fillWidth: true

            TextField {
                id: startDateField
                placeholderText: "Start Date (YYYY-MM-DD)"
                text: "2025-01-01"
                Layout.preferredWidth: 200  // Daha dar
            }

            TextField {
                id: endDateField
                placeholderText: "End Date (YYYY-MM-DD)"
                text: "2025-04-20"
                Layout.preferredWidth: 200  // Daha dar
            }

            Button {
                text: "Detect Collusion"
                Layout.preferredWidth: 180  // Biraz dar
                onClicked: {
                    collusionHandler.detectCollusion(startDateField.text, endDateField.text)
                }
            }

            // Boşluk bırakıyoruz ➔ Sağdaki butonu ayırıyor
            Item {
                Layout.fillWidth: true
            }

            Button {
                text: "Main Menu"
                Layout.preferredWidth: 150
                onClicked: {
                    collusionHandler.goBackToMainMenu()
                }
            }
        }

        Rectangle {
            id: outputArea
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: "#004d40"
            radius: 10

            ScrollView {
                anchors.fill: parent
                clip: true

                Column {
                    id: outputColumn
                    spacing: 8
                    anchors.left: parent.left
                    anchors.right: parent.right

                    Repeater {
                        model: collusionHandler.outputModel

                        Text {
                            text: model.display
                            color: "white"
                            font.pixelSize: 14
                            wrapMode: Text.WrapAnywhere
                            horizontalAlignment: Text.AlignLeft
                        }
                    }
                }
            }
        }
    }
}
