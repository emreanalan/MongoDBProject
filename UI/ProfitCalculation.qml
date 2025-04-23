import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

ApplicationWindow {
    id: profitCalculationWindow
    visible: true
    width: 1100
    height: 700
    title: "Profit Calculation"
    color: "#003333"

    Component.onCompleted: {
        profitCalculationHandler.loadManufacturers()
        profitCalculationHandler.closePopup.connect(loadingPopup.close)
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

        // === ÜSTTE İKİ SATIR (2 Row, 5 Column GridLayout) ===
        GridLayout {
            id: topGrid
            columns: 5
            rowSpacing: 10
            columnSpacing: 10
            Layout.fillWidth: true

            // Row 1
            Label {
                text: "Start Date:"
                color: "White"
                verticalAlignment: Text.AlignVCenter
            }

            TextField {
                id: startDateField
                placeholderText: "YYYY-MM-DD"
                text: "2025-01-01"
                Layout.fillWidth: true
            }

            ComboBox {
                id: manufacturerCombo
                Layout.fillWidth: true
                model: profitCalculationHandler.manufacturerModel
                textRole: "display"
                contentItem: Text {
                    text: parent.currentText
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignHCenter
                }
                onActivated: {
                    console.log("Activated:", manufacturerCombo.currentText)
                    if (manufacturerCombo.currentText !== "") {
                        loadingText.text = "Loading shops for " + manufacturerCombo.currentText + "..."
                        loadingPopup.open()
                        profitCalculationHandler.loadShopsForManufacturer(manufacturerCombo.currentText)
                    }
                }
            }
            ComboBox {
                id: shopCombo
                Layout.fillWidth: true
                model: profitCalculationHandler.shopModel
                textRole: "display"
                contentItem: Text {
                    text: parent.currentText
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignHCenter
                }
                onActivated: {
                    console.log("Selected shop:", shopCombo.currentText)
                    // Eğer ileride bir işlem yapılacaksa burada çağrılır
                }
            }

            Button {
                text: "General Stats"
                Layout.fillWidth: true
                onClicked: {
                    profitCalculationHandler.showGeneralStats()
                }
            }

            // Row 2
            Label {
                text: "End Date:"
                color: "White"
                verticalAlignment: Text.AlignVCenter
            }

            TextField {
                id: endDateField
                placeholderText: "YYYY-MM-DD"
                text: "2025-04-20"
                Layout.fillWidth: true
            }

            Button {
                text: "Calculate Manufacturer Profit"
                Layout.fillWidth: true
                onClicked: {
                    profitCalculationHandler.calculateProfitForManufacturer(
                        startDateField.text,
                        endDateField.text,
                        manufacturerCombo.currentText
                    )
                }
            }

            Button {
                text: "Calculate Shop Profit"
                Layout.fillWidth: true
                onClicked: {
                    profitCalculationHandler.calculateProfitForShop(
                        startDateField.text,
                        endDateField.text,
                        manufacturerCombo.currentText,
                        shopCombo.currentText
                    )
                }
            }

            Button {
                text: "Main Menu"
                Layout.fillWidth: true
                onClicked: {
                    profitCalculationHandler.goBackToMainMenu()
                }
            }
        }

        // === ALTTA ÇIKTI ALANI ===
        Rectangle {
            id: outputArea
            color: "#004d40"
            Layout.fillWidth: true
            Layout.fillHeight: true
            radius: 10

            ScrollView {
                anchors.fill: parent
                clip: true

                ListView {
                    id: outputListView
                    width: parent.width
                    model: profitCalculationHandler.outputModel

                    delegate: Text {
                        text: model.display
                        color: "White"
                        wrapMode: Text.WrapAnywhere
                        font.pixelSize: 14
                        anchors.horizontalCenter: parent.horizontalCenter
                    }
                }
            }
        }
    }
}
