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
        id: addProductForm
        Label {
            text: "Add Product Screen"
            color: "white"
            anchors.centerIn: parent
        }
    }

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

}
