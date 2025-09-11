#include <QGuiApplication>
#include <QQmlApplicationEngine>
#include <QtWebView>

int main(int argc, char *argv[])
{
    QGuiApplication app(argc, argv);

    QtWebView::initialize();

    QQmlApplicationEngine engine;
    QObject::connect(
        &engine,
        &QQmlApplicationEngine::objectCreationFailed,
        &app,
        []() { QCoreApplication::exit(-1); },
        Qt::QueuedConnection);
    engine.loadFromModule("RegPacQt", "Main");

    return app.exec();
}
