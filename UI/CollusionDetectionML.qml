import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

ApplicationWindow {
    id: mlCollusionDetectionWindow
    visible: true
    width: 1200
    height: 1000
    title: "ML Collusion Detection"
    color: "#003333"

    ColumnLayout {
        anchors.fill: parent
        spacing: 10
        anchors.margins: 20

        // Üst kısım: sadece başlık ve menüye dönüş
        RowLayout {
            spacing: 10
            Layout.fillWidth: true

            Text {
                text: "📊 Machine Learning-Based Collusion Detection"
                color: "white"
                font.bold: true
                font.pixelSize: 20
                Layout.alignment: Qt.AlignLeft
            }

            Item {
                Layout.fillWidth: true
            }

            Button {
                text: "Main Menu"
                Layout.preferredWidth: 150
                onClicked: mlHandler.goBackToMainMenu()
            }
        }

        // Alt kısım: Model çıktıları
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
                        model: mlHandler.outputModel

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
