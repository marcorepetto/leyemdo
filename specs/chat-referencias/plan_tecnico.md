# Plan Técnico: Spec 8 - Interfaz de Chat y Referencias

Este plan técnico detalla los cambios de software, las APIs de red en C++ para la ingesta asíncrona, la navegación de páginas de Okular KPart y el consumo del chat de IA en streaming en React.

---

## 1. Archivos Impactados

### A. Subproyecto C++ (Visor)
```text
visor/
└── src/
    ├── jsbridge.h              # Modificar: Añadir slots para hash, ingesta, navegación y señal de progreso
    ├── jsbridge.cpp            # Modificar: Implementar hash (SHA-256), QNetworkAccessManager POST e IPC
    ├── mainwindow.h            # Modificar: Añadir funciones y slots de soporte de navegación
    └── mainwindow.cpp          # Modificar: Conectar señales del JSBridge y navegar páginas del PDF
```

### B. Subproyecto React (Frontend en `/frontend/`)
```text
frontend/
└── src/
    ├── App.tsx                 # Modificar: Lógica de inicialización e IPC
    ├── qwebchannel.ts          # Modificar: Declarar tipos de los nuevos métodos expuestos
    └── components/
        └── ChatPanel.tsx       # Crear: Componente de chat, historial, ingesta guiada y referencias
```

---

## 2. Detalle de los Cambios C++

### A. Puente de Ingesta Asíncrona (`jsbridge.h` y `jsbridge.cpp`)
El puente calculará el hash SHA-256 del PDF y subirá el archivo mediante multipart HTTP en segundo plano si no está indexado.

* **Firma en `jsbridge.h`:**
```cpp
public slots:
    // Retorna el hash SHA-256 de un archivo local
    QString getFileHash(const QString &filePath);
    
    // Inicia la carga HTTP POST multipart de un archivo
    void ingestDocument(const QString &filePath, const QString &documentId);
    
    // Desplaza el visor PDF a una página específica
    void scrollToPage(int pageNumber);

signals:
    // Emite actualizaciones del estado y progreso de la carga a React
    void ingestStatus(const QString &documentId, const QString &status, double progress, const QString &error);
```

* **Cálculo de Hash SHA-256 (`jsbridge.cpp`):**
```cpp
#include <QCryptographicHash>
#include <QFile>

QString JSBridge::getFileHash(const QString &filePath)
{
    QFile file(filePath);
    if (!file.open(QIODevice::ReadOnly)) {
        return QString();
    }
    QCryptographicHash hash(QCryptographicHash::Sha256);
    if (hash.addData(&file)) {
        return hash.result().toHex();
    }
    return QString();
}
```

* **Carga de Archivo por Red (IPC Ingest):**
Utilizaremos `QNetworkAccessManager` y `QHttpMultiPart` para enviar el PDF de forma asíncrona:
```cpp
#include <QNetworkAccessManager>
#include <QNetworkReply>
#include <QHttpMultiPart>

void JSBridge::ingestDocument(const QString &filePath, const QString &documentId)
{
    QFile *file = new QFile(filePath, this);
    if (!file->open(QIODevice::ReadOnly)) {
        emit ingestStatus(documentId, QStringLiteral("error"), 0, QStringLiteral("No se pudo abrir el archivo local."));
        return;
    }

    QNetworkAccessManager *manager = new QNetworkAccessManager(this);
    QHttpMultiPart *multiPart = new QHttpMultiPart(QHttpMultiPart::FormDataType, this);

    QHttpPart filePart;
    filePart.setHeader(QNetworkRequest::ContentDispositionHeader, 
                       QVariant(QString("form-data; name=\"file\"; filename=\"%1\"").arg(file->fileName())));
    filePart.setBodyDevice(file);
    file->setParent(multiPart); // Vincular ciclo de vida del archivo al multipart
    multiPart->append(filePart);

    QUrl url(QStringLiteral("http://localhost:8000/api/v1/documents/upload"));
    QNetworkRequest request(url);

    QNetworkReply *reply = manager->post(request, multiPart);
    multiPart->setParent(reply);

    // Reportar progreso de carga
    connect(reply, &QNetworkReply::uploadProgress, [this, documentId](qint64 bytesSent, qint64 bytesTotal) {
        double progress = bytesTotal > 0 ? (double)bytesSent / bytesTotal : 0.0;
        emit ingestStatus(documentId, QStringLiteral("processing"), progress, QString());
    });

    // Finalización
    connect(reply, &QNetworkReply::finished, [this, reply, documentId]() {
        if (reply->error() == QNetworkReply::NoError) {
            emit ingestStatus(documentId, QStringLiteral("completed"), 1.0, QString());
        } else {
            emit ingestStatus(documentId, QStringLiteral("error"), 0.0, reply->errorString());
        }
        reply->deleteLater();
    });
}
```

### B. Navegación en el Visor (`mainwindow.cpp`)
El desplazamiento se realiza invocando a `openUrl` con un fragmento `#pageNumber`:
```cpp
void JSBridge::scrollToPage(int pageNumber)
{
    // Emitir señal interna hacia MainWindow
    emit pageNavigationRequested(pageNumber);
}
```
En `MainWindow`:
```cpp
// Conectar en setupVisor()
connect(m_bridge, &JSBridge::pageNavigationRequested, this, &MainWindow::scrollToPage);

void MainWindow::scrollToPage(int pageNumber)
{
    if (m_part && !m_currentFilePath.isEmpty()) {
        QUrl url = QUrl::fromLocalFile(m_currentFilePath);
        url.setFragment(QString::number(pageNumber));
        m_part->openUrl(url);
    }
}
```

---

## 3. Detalle de los Cambios React

### A. Consumo de Streaming SSE (Native ReadableStream)
Consumiremos el endpoint asíncrono leyendo el stream de respuesta chunk a chunk:
```typescript
const response = await fetch("http://localhost:8000/api/v1/chat/message", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ document_id: docId, message: text })
});

const reader = response.body?.getReader();
const decoder = new TextDecoder();
// Bucle asíncrono para decodificar y añadir el fragmento al chat en tiempo real...
```

### B. Renderizado de Referencias Bibliográficas
1. Al cargar un documento, React llama a `GET /api/v1/documents/chunks/{document_id}` para obtener los metadatos y la bibliografía.
2. Al recibir respuestas, reemplazamos patrones tipo `[X]` por elementos cliqueables `<span className="citation-link">[X]</span>`.
3. Al hacer clic o hover, mostramos un Popover con:
   - Título y detalle de la referencia desde los metadatos bibliográficos globales.
   - Botón *"Ir a la página"* que invoca `window.qtBridge.scrollToPage(pageNum)`.

---

## 4. Próxima Fase (Fase 3: Plan de Implementación)
Tras recibir la aprobación del plan técnico:
1. Realizaremos un **commit en git** con el plan técnico aprobado.
2. Escribiremos el **Plan de Implementación** detallando los comandos y cambios a realizar.
