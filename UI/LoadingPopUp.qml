import QtQuick 2.15
import QtQuick.Controls 2.15

Popup {
    id: loadingPopup
    width: 300
    height: 100
    modal: true
    focus: true
    closePolicy: Popup.NoAutoClose
    dim: true
    background: Rectangle {
        color: "#333"
        radius: 10
    }

    Column {
        anchors.centerIn: parent
        spacing: 10

        Text {
            id: loadingText
            text: "Working..."
            color: "white"
            font.pixelSize: 16
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
        }
    }
}

// Bu QML dosyasını FraudDetection.qml, CollusionDetection.qml gibi her yerde import ederek kullanabilirsin.
// Açmak için: loadingPopup.open();
// Yazısını değiştirmek için: loadingText.text = "Working on Detect ML Fraud, please wait...";
// Kapatmak için: loadingPopup.close();
