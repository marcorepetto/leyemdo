#include "jsbridge.h"
#include <QDebug>
#include <QCryptographicHash>
#include <QFile>
#include <QNetworkAccessManager>
#include <QNetworkReply>
#include <QHttpMultiPart>
#include <QHttpPart>
#include <QUrl>
#include <QNetworkRequest>

JSBridge::JSBridge(QObject *parent)
    : QObject(parent)
{
}

void JSBridge::postMessage(const QString &message)
{
    qInfo() << "IPC: Mensaje recibido desde JavaScript:" << message;
    emit messageReceived(message);
}

QString JSBridge::getFileHash(const QString &filePath)
{
    QFile file(filePath);
    if (!file.open(QIODevice::ReadOnly)) {
        qWarning() << "No se pudo abrir el archivo para hash:" << filePath;
        return QString();
    }
    QCryptographicHash hash(QCryptographicHash::Sha256);
    if (hash.addData(&file)) {
        return hash.result().toHex();
    }
    return QString();
}

void JSBridge::ingestDocument(const QString &filePath, const QString &documentId)
{
    qInfo() << "IPC: Iniciando ingesta para:" << filePath << "con ID:" << documentId;
    
    QFile *file = new QFile(filePath, this);
    if (!file->open(QIODevice::ReadOnly)) {
        qWarning() << "No se pudo abrir el archivo para ingesta:" << filePath;
        emit ingestStatus(documentId, QStringLiteral("error"), 0.0, QStringLiteral("No se pudo abrir el archivo local."));
        file->deleteLater();
        return;
    }

    QNetworkAccessManager *manager = new QNetworkAccessManager(this);
    QHttpMultiPart *multiPart = new QHttpMultiPart(QHttpMultiPart::FormDataType, this);

    QHttpPart filePart;
    // Okular-part o el sistema de archivos puede retornar nombres con rutas. Extraer el nombre base del archivo.
    QString baseName = filePath.section(QLatin1Char('/'), -1);
    filePart.setHeader(QNetworkRequest::ContentDispositionHeader, 
                       QVariant(QString("form-data; name=\"file\"; filename=\"%1\"").arg(baseName)));
    filePart.setBodyDevice(file);
    file->setParent(multiPart); // El archivo se destruirá con el multipart
    multiPart->append(filePart);

    QUrl url(QStringLiteral("http://localhost:8000/api/v1/documents/upload"));
    QNetworkRequest request(url);

    QNetworkReply *reply = manager->post(request, multiPart);
    multiPart->setParent(reply); // El multipart se destruirá con la respuesta

    // Conectar el progreso de subida
    connect(reply, &QNetworkReply::uploadProgress, [this, documentId](qint64 bytesSent, qint64 bytesTotal) {
        double progress = bytesTotal > 0 ? (double)bytesSent / bytesTotal : 0.0;
        emit ingestStatus(documentId, QStringLiteral("processing"), progress, QString());
    });

    // Conectar la finalización
    connect(reply, &QNetworkReply::finished, [this, reply, documentId]() {
        if (reply->error() == QNetworkReply::NoError) {
            qInfo() << "IPC: Ingesta completada con éxito para:" << documentId;
            emit ingestStatus(documentId, QStringLiteral("completed"), 1.0, QString());
        } else {
            qWarning() << "IPC: Error cargando el archivo:" << reply->errorString();
            emit ingestStatus(documentId, QStringLiteral("error"), 0.0, reply->errorString());
        }
        reply->deleteLater();
    });
}

void JSBridge::scrollToPage(int pageNumber)
{
    qInfo() << "IPC: Navegación de página solicitada:" << pageNumber;
    emit pageNavigationRequested(pageNumber);
}

QString JSBridge::currentFilePath() const
{
    return m_currentFilePath;
}

QString JSBridge::currentDocumentId() const
{
    return m_currentDocumentId;
}

#include <QSettings>

void JSBridge::setCurrentFile(const QString &filePath, const QString &documentId)
{
    m_currentFilePath = filePath;
    m_currentDocumentId = documentId;
    
    if (!filePath.isEmpty() && !documentId.isEmpty()) {
        QSettings settings(QStringLiteral("LectorInteligente"), QStringLiteral("Visor"));
        settings.setValue(QString("paths/%1").arg(documentId), filePath);
        qInfo() << "IPC: Mapeo de ruta local guardado para hash:" << documentId << "->" << filePath;
    }
}

void JSBridge::openDocumentFromReact(const QString &documentId)
{
    qInfo() << "IPC: Solicitada apertura de archivo desde React para ID:" << documentId;
    QSettings settings(QStringLiteral("LectorInteligente"), QStringLiteral("Visor"));
    QString filePath = settings.value(QString("paths/%1").arg(documentId)).toString();
    
    if (!filePath.isEmpty() && QFile::exists(filePath)) {
        qInfo() << "IPC: Encontrado archivo local para abrir:" << filePath;
        emit openDocumentRequested(filePath);
    } else {
        qWarning() << "IPC: No se encontró la ruta del archivo local o el archivo no existe:" << filePath;
    }
}

void JSBridge::setCurrentTab(int tabIndex)
{
    qInfo() << "IPC: Cambio de pestaña solicitado desde React:" << tabIndex;
    emit currentTabChangeRequested(tabIndex);
}

#include <QFileDialog>

void JSBridge::importDocumentFromReact()
{
    qInfo() << "IPC: Abriendo diálogo de selección para importar PDF...";
    QString filePath = QFileDialog::getOpenFileName(nullptr,
                                                    tr("Importar PDF a Biblioteca"),
                                                    QString(),
                                                    tr("Archivos PDF (*.pdf)"));
    if (filePath.isEmpty()) {
        qInfo() << "IPC: Importación cancelada por el usuario.";
        return;
    }

    QString documentId = getFileHash(filePath);
    if (documentId.isEmpty()) {
        qWarning() << "IPC: No se pudo generar hash para el archivo:" << filePath;
        return;
    }

    // Registrar mapeo local
    QSettings settings(QStringLiteral("LectorInteligente"), QStringLiteral("Visor"));
    settings.setValue(QString("paths/%1").arg(documentId), filePath);
    qInfo() << "IPC: Mapeo guardado para importación:" << documentId << "->" << filePath;

    // Disparar proceso de ingesta asíncrono
    ingestDocument(filePath, documentId);
}
