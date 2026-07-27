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
    
    // Retorna el hash SHA-256 de un archivo local
    QString getFileHash(const QString &filePath);
    
    // Inicia la carga asíncrona de un archivo local
    void ingestDocument(const QString &filePath, const QString &documentId);
    
    // Solicita la navegación a una página
    void scrollToPage(int pageNumber);

    // Métodos invocables desde JS para obtener el archivo actual en carga inicial (evita race conditions)
    QString currentFilePath() const;
    QString currentDocumentId() const;

    // Método C++ para actualizar el archivo activo
    void setCurrentFile(const QString &filePath, const QString &documentId);

    // Slots llamados desde la biblioteca de React
    void openDocumentFromReact(const QString &documentId);
    void setCurrentTab(int tabIndex);
    void importDocumentFromReact();

signals:
    // Señal emitida a C++ cuando llega un mensaje de JS
    void messageReceived(const QString &message);

    // Señal enviada a JS cuando se abre un PDF en C++ (incluye el documentId/hash)
    void fileLoaded(const QString &filePath, const QString &documentId);

    // Señal de progreso de ingesta enviada a JS
    void ingestStatus(const QString &documentId, const QString &status, double progress, const QString &error);

    // Señal emitida internamente a MainWindow para cambiar de página
    void pageNavigationRequested(int pageNumber);

    // Señales emitidas a MainWindow desde la biblioteca
    void openDocumentRequested(const QString &filePath);
    void currentTabChangeRequested(int tabIndex);

private:
    QString m_currentFilePath;
    QString m_currentDocumentId;
};
