import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

ApplicationWindow {
    visible: true
    width: 1000
    height: 700
    title: "Dynamic Product Handling"
    color: "#003333"

    ColumnLayout {
        anchors.fill: parent
        spacing: 10
        anchors.margins: 20

        // Üst Butonlar
        GridLayout {
            id: buttonGrid
            columns: 4
            columnSpacing: 10
            rowSpacing: 10
            Layout.fillWidth: true

            Button {
                text: "➕ Add Product"
                Layout.fillWidth: true
                onClicked: {
                    dynamicHandler.loadProducts()
                    dynamicArea.state = "addProduct"
                }
            }

            Button {
                text: "🏭 Add Manufacturer"
                Layout.fillWidth: true
                onClicked: {
                    dynamicArea.state = "addManufacturer"
                }
            }

            Button {
                text: "🏪 Add Shop"
                Layout.fillWidth: true
                onClicked: {
                    dynamicArea.state = "addShop"
                }
            }

            Button {
                text: "🤝 Add Collusion Shop"
                Layout.fillWidth: true
                onClicked: {
                    dynamicArea.state = "addCollusionShop"
                }
            }

            Button {
                text: "🗑 Delete Data"
                Layout.fillWidth: true
                onClicked: {
                    dynamicArea.state = "deleteData"
                }
            }

            Button {
                text: "📜 List Products"
                Layout.fillWidth: true
                onClicked: {
                    dynamicHandler.loadProducts()
                    dynamicArea.state = "listProducts"
                }
            }

            Button {
                text: "📜 List Shops (takes 1 min)"
                Layout.fillWidth: true
                onClicked: {
                    dynamicHandler.loadUniqueShops()
                    dynamicArea.state = "listShops"
                }
            }

            Button {
                text: "📜 List Manufacturers"
                Layout.fillWidth: true
                onClicked: {
                    dynamicHandler.loadManufacturers()
                    dynamicArea.state = "listManufacturers"
                }
            }

            Button {
                text: "🏠 Back to Main Menu"
                Layout.fillWidth: true
                onClicked: {
                    dynamicHandler.goBackToMainMenu()
                }
            }
        }

        // Alt Dinamik Alan
        Rectangle {
            id: dynamicArea
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: "#004d40"
            radius: 10

            // State'ler
            states: [
                State {
                    name: "addProduct"
                    PropertyChanges { target: contentLoader; sourceComponent: addProductForm }
                },
                State {
                    name: "addManufacturer"
                    PropertyChanges { target: contentLoader; sourceComponent: addManufacturerForm }
                },
                State {
                    name: "addShop"
                    PropertyChanges { target: contentLoader; sourceComponent: addShopForm }
                },
                State {
                    name: "addCollusionShop"
                    PropertyChanges { target: contentLoader; sourceComponent: addCollusionShopForm }
                },
                State {
                    name: "deleteData"
                    PropertyChanges { target: contentLoader; sourceComponent: deleteDataForm }
                },
                State {
                    name: "listProducts"
                    PropertyChanges { target: contentLoader; sourceComponent: listProductsForm }
                },
                State {
                    name: "listShops"
                    PropertyChanges { target: contentLoader; sourceComponent: listShopsForm }
                },
                State {
                    name: "listManufacturers"
                    PropertyChanges { target: contentLoader; sourceComponent: listManufacturersForm }
                }
            ]

            // İçerik Loader
            Loader {
                id: contentLoader
                anchors.fill: parent
            }
        }
    }

    // COMPONENTS ==========================

    Component {
        id: addManufacturerForm
        Label {
            text: "Add Manufacturer Screen"
            color: "white"
            anchors.centerIn: parent
        }
    }

    Component {
        id: addShopForm
        Label {
            text: "Add Shop Screen"
            color: "white"
            anchors.centerIn: parent
        }
    }

    Component {
        id: addCollusionShopForm
        Label {
            text: "Add Collusion Shop Screen"
            color: "white"
            anchors.centerIn: parent
        }
    }

    Component {
        id: deleteDataForm
        Label {
            text: "Delete Data Screen"
            color: "white"
            anchors.centerIn: parent
        }
    }
    Component {
        id: listProductsForm

        Rectangle {
            color: "#004d40"
            anchors.fill: parent

            ListView {
                id: productListView
                anchors.fill: parent
                model: dynamicHandler.productListModel

                delegate: Rectangle {
                    width: parent.width
                    height: 50
                    color: "#006d5b"
                    radius: 8
                    border.color: "white"
                    border.width: 1
                    anchors.margins: 5

                    Text {
                        anchors.centerIn: parent
                        text: model.display
                        color: "white"
                        font.pixelSize: 16
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                }

                spacing: 8
                clip: true
            }

        }
    }

    Component {
        id: listShopsForm

        Rectangle {
            color: "#004d40"
            anchors.fill: parent

            ListView {
                id: productListView
                anchors.fill: parent
                model: dynamicHandler.productListModel

                delegate: Rectangle {
                    width: parent.width
                    height: 50
                    color: "#006d5b"
                    radius: 8
                    border.color: "white"
                    border.width: 1
                    anchors.margins: 5

                    Text {
                        anchors.centerIn: parent
                        text: model.display
                        color: "white"
                        font.pixelSize: 16
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                }

                spacing: 8
                clip: true
            }

        }
    }



    Component {
        id: listManufacturersForm

        Rectangle {
            color: "#004d40"
            anchors.fill: parent

            ListView {
                id: productListView
                anchors.fill: parent
                model: dynamicHandler.productListModel

                delegate: Rectangle {
                    width: parent.width
                    height: 50
                    color: "#006d5b"
                    radius: 8
                    border.color: "white"
                    border.width: 1
                    anchors.margins: 5

                    Text {
                        anchors.centerIn: parent
                        text: model.display
                        color: "white"
                        font.pixelSize: 16
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                }

                spacing: 8
                clip: true
            }

        }
    }
/*
    Component {
        id: addProductForm

        Rectangle {
            color: "#004d40"
            anchors.fill: parent
            property var materialInputs: {}

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 20
                spacing: 10

                Label {
                    text: "Product Name:"
                    color: "white"
                }

                TextField {
                    id: productNameField
                    placeholderText: "Enter product name..."
                    Layout.fillWidth: true
                }

                Flickable {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    minimumHeight: 300
                    contentHeight: columnContent.height
                    clip: true

                    Column {
                        id: columnContent
                        spacing: 10
                        Layout.fillWidth: true

                        property var materials: [
                            "Aluminum 1Kg", "Copper 1Kg", "Gold 1Kg", "Silver 1Kg",
                            "Ham_Petrol_Fiyati 1L", "Elektrik_Ucreti 1kW", "Asgari_Ucret 1 iş günü",
                            "Dogal_Gaz 100m^3", "USD", "EUR"
                        ]

                        Repeater {
                            model: materials
                            delegate: RowLayout {
                                spacing: 10
                                Label {
                                    text: modelData
                                    color: "white"
                                    width: 200
                                }

                                TextField {
                                    id: tf
                                    width: 100
                                    placeholderText: "0.0"
                                    inputMethodHints: Qt.ImhFormattedNumbersOnly

                                    Component.onCompleted: {
                                        addProductForm.materialInputs[modelData] = tf
                                    }
                                }
                            }
                        }
                    }
                }

                RowLayout {
                    Layout.alignment: Qt.AlignRight
                    spacing: 10

                    BusyIndicator {
                        id: loadingIndicator
                        running: false
                        visible: false
                    }

                    Button {
                        text: "Create Product"
                        onClicked: {
                            let productName = productNameField.text.trim();
                            if (productName === "") {
                                console.log("Product name is required.");
                                return;
                            }

                            let materials = {};
                            for (let key in addProductForm.materialInputs) {
                                let value = parseFloat(addProductForm.materialInputs[key].text);
                                if (!isNaN(value)) {
                                    materials[key] = value;
                                }
                            }

                            loadingIndicator.running = true;
                            loadingIndicator.visible = true;

                            dynamicHandler.createProduct(productName, materials);

                            Qt.callLater(() => {
                                loadingIndicator.running = false;
                                loadingIndicator.visible = false;
                            });
                        }
                    }
                }
            }
        }
    } */
}
