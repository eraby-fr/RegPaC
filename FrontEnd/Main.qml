import QtQuick
import QtQuick.Controls
import QtWebView
import QtQuick.Layouts

Window {
    id: mainWindow
    width: 320
    height: 480
    visible: true
    title: qsTr("RegPac Home")
    color: "black"

    Column {
        anchors.fill: parent
        spacing: 0
        padding: 0

        WebView {
            id: webview
            width: parent.width
            height: parent.height - 100 // ajuste la hauteur pour laisser de la place aux boutons
            //url: "http://192.168.0.3:3000/d/heatregul/home?orgId=1&from=now-1d&to=now&timezone=browser&refresh=1m&viewPanel=panel-2&fullscreen&kiosk&_dash.hideTimePicker"
            url: "http://192.168.0.3:3000/d/fekb3rq1dp6v4c/mobile?orgId=1&from=now-24h&to=now&timezone=browser&fullscreen&kiosk&_dash.hideTimePicker"
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 5  // <<< ESPACEMENT de 5 entre les éléments
            height: 30

            Slider {
                id: slider
                Layout.fillWidth: true
                from: 17
                to: 24
                stepSize: 1
                value: 17 // valeur initiale
                onValueChanged: {
                    valueText.text = slider.value.toFixed(0);

                    var comfort = parseInt(slider.value);
                    var eco = comfort - 1;

                    var xhr = new XMLHttpRequest();
                    xhr.open("POST", "http://192.168.0.3:80/setpoint");
                    xhr.setRequestHeader("Content-Type", "application/json");

                    var payload = {
                        comfort_temp: comfort,
                        eco_temp: eco
                    };

                    xhr.onreadystatechange = function() {
                        if (xhr.readyState === XMLHttpRequest.DONE) {
                            if (xhr.status === 200 || xhr.status === 201) {
                                console.log("POST réussi:", xhr.responseText);
                                postexitcode.text = "POST réussi"
                            } else {
                                console.log("Erreur POST:", xhr.status);
                                postexitcode.text = "Erreur POST"
                            }
                        }
                    }

                    xhr.send(JSON.stringify(payload));
                }
            }

            Text {
                id: valueText
                text: slider.value.toFixed(0)
                color: "white"
                font.pixelSize: 24
                horizontalAlignment: Text.AlignHRight
                Layout.alignment: Qt.AlignHRight
            }
            Text {
                id: postexitcode
                text: ""
                color: "white"
                font.pixelSize: 24
                horizontalAlignment: Text.AlignHRight
                Layout.alignment: Qt.AlignHRight
            }
        }
    }
}
