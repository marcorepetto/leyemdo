#include "jsbridge.h"
#include <QDebug>

JSBridge::JSBridge(QObject *parent)
    : QObject(parent)
{
}

void JSBridge::postMessage(const QString &message)
{
    qInfo() << "IPC: Mensaje recibido desde JavaScript:" << message;
    emit messageReceived(message);
}
