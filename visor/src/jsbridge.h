#pragma once

#include <QObject>

class JSBridge : public QObject
{
    Q_OBJECT

public:
    explicit JSBridge(QObject *parent = nullptr);

public slots:
    // Slot invocado desde JavaScript
    void postMessage(const QString &message);

signals:
    // Señal emitida a C++ cuando llega un mensaje de JS
    void messageReceived(const QString &message);

    // Señal enviada a JS cuando se abre un PDF en C++
    void fileLoaded(const QString &filePath);
};
