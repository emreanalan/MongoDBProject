import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

ApplicationWindow {
    id: fraudDetectionWindow
    visible: true
    width: 1200
    height: 800
    title: "Fraud Detection"
    color: "#003333"

    Connections {
        target: FraudHandler
        function onClosePopup() {
            loadingPopup.close()
        }
    }

    // Loading Popup
    Popup {
        id: loadingPopup
        modal: true
        focus: true
        dim: true
        width: 300
        height: 150
        closePolicy: Popup.NoAutoClose
        anchors.centerIn: parent

        Rectangle {
            anchors.fill: parent
            color: "#002b36"
            radius: 10

            Column {
                anchors.centerIn: parent
                spacing: 10

                BusyIndicator {
                    running: true
                }

                Text {
                    id: loadingText
                    text: "Processing, please wait..."
                    color: "white"
                    font.pixelSize: 14
                    wrapMode: Text.WordWrap
                    horizontalAlignment: Text.AlignHCenter
                }
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 10
        anchors.margins: 20

        GridLayout {
            columns: 5
            columnSpacing: 10
            rowSpacing: 10
            Layout.fillWidth: true

            // Row 1
            Text { text: "Start Date:"; color: "white" }
            TextField {
                id: startDateField
                placeholderText: "YYYY-MM-DD"
                text: "2025-01-01"
                Layout.preferredWidth: 150
            }
            Button {
                text: "Detect ML Fraud"
                onClicked: {
                    loadingText.text = "Working on Detect ML Fraud, please wait..."
                    loadingPopup.open()
                    FraudHandler.detectMLFraud(startDateField.text, endDateField.text)
                }
            }
            Item { Layout.fillWidth: true }
            Button {
                text: "Main Menu"
                onClicked: FraudHandler.goBackToMainMenu()
            }

            // Row 2
            Text { text: "End Date:"; color: "white" }
            TextField {
                id: endDateField
                placeholderText: "YYYY-MM-DD"
                text: "2025-04-20"
                Layout.preferredWidth: 150
            }
            Button {
                text: "Detect Rule-Based Fraud"
                onClicked: {
                    //loadingText.text = "Working on Detect Rule-Based Fraud, please wait..."
                    //loadingPopup.open()
                    FraudHandler.detectRuleFraud(startDateField.text, endDateField.text, maxProfitField.text)
                }
            }
            RowLayout {
                spacing: 5
                Text { text: "Maks Profit:"; color: "white" }
                TextField {
                    id: maxProfitField
                    placeholderText: "%"
                    text: "6"
                    Layout.preferredWidth: 30
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
                        model: FraudHandler.outputModel

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

    Component.onCompleted: FraudHandler.closePopup.connect(loadingPopup.close)
}
