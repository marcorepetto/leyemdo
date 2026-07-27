#include "mainwindow.h"
#include <KParts/PartLoader>
#include <KParts/ReadOnlyPart>
#include <QHBoxLayout>
#include <QMessageBox>
#include <QDebug>
#include <QTabWidget>
#include <QWebEngineView>
#include <QWebChannel>
#include <QSplitter>
#include <QStatusBar>
#include "jsbridge.h"

MainWindow::MainWindow(QWidget *parent)
    : KParts::MainWindow(parent)
    , m_part(nullptr)
    , m_tabWidget(nullptr)
    , m_chatView(nullptr)
    , m_libraryView(nullptr)
    , m_channel(nullptr)
    , m_bridge(nullptr)
{
    setupVisor();
}

MainWindow::~MainWindow()
{
}

void MainWindow::setupVisor()
{
    // Crear el widget central como QTabWidget
    m_tabWidget = new QTabWidget(this);
    setCentralWidget(m_tabWidget);

    // Determinar la URL base para el frontend de React
    // Si la variable de entorno DEV_URL está seteada, la usamos; si no, http://localhost:5173 por defecto.
    QString baseWebUrl = QString::fromLocal8Bit(qgetenv("DEV_URL"));
    if (baseWebUrl.isEmpty()) {
        baseWebUrl = QStringLiteral("http://localhost:5173");
    }

    // Inicializar puente IPC (WebChannel)
    m_channel = new QWebChannel(this);
    m_bridge = new JSBridge(this);
    m_channel->registerObject(QStringLiteral("qtBridge"), m_bridge);
    
    // Conectar el mensaje recibido de JS a un slot de MainWindow
    connect(m_bridge, &JSBridge::messageReceived, this, &MainWindow::handleJSMessage);

    // --- PESTAÑA 1: DOCUMENTO Y CHAT ---
    QWidget *tabReader = new QWidget(m_tabWidget);
    QHBoxLayout *readerLayout = new QHBoxLayout(tabReader);
    readerLayout->setContentsMargins(0, 0, 0, 0);

    QSplitter *splitter = new QSplitter(Qt::Horizontal, tabReader);
    readerLayout->addWidget(splitter);

    // Cargar Okular KPart
    auto result = KParts::PartLoader::instantiatePartForMimeType<KParts::ReadOnlyPart>(
        QStringLiteral("application/pdf"), tabReader, this
    );

    if (result) {
        m_part = result.plugin;
        splitter->addWidget(m_part->widget());

        // Configurar el chat view
        m_chatView = new QWebEngineView(tabReader);
        m_chatView->page()->setWebChannel(m_channel);
        m_chatView->load(QUrl(baseWebUrl + QStringLiteral("/chat")));
        splitter->addWidget(m_chatView);

        // Establecer proporciones iniciales en el splitter (70% PDF, 30% Chat)
        QList<int> sizes;
        sizes << 700 << 300;
        splitter->setSizes(sizes);

        // Inicializar la GUI de KDE KParts
        setupGUI();
        createGUI(m_part);

        // Agregar pestaña lector
        m_tabWidget->addTab(tabReader, tr("Documento"));
    } else {
        qCritical() << "No se pudo cargar el KPart de Okular para PDF:" << result.errorText;
        QMessageBox::critical(this, tr("Error de Carga"),
            tr("No se pudo encontrar o cargar el plugin de visor de PDF de Okular. "
               "Asegúrate de tener instalado el paquete 'okular-part'.\nDetalle: ") + result.errorText);
    }

    // --- PESTAÑA 2: BIBLIOTECA (FULLSCREEN REACT) ---
    m_libraryView = new QWebEngineView(m_tabWidget);
    m_libraryView->page()->setWebChannel(m_channel);
    m_libraryView->load(QUrl(baseWebUrl + QStringLiteral("/library")));
    m_tabWidget->addTab(m_libraryView, tr("Biblioteca"));

    // Configurar ventana
    setWindowTitle(tr("Lector PDF Inteligente"));
    resize(1200, 800);
}

void MainWindow::openDocument(const QString &filePath)
{
    m_currentFilePath = filePath;
    if (m_part && !filePath.isEmpty()) {
        m_part->openUrl(QUrl::fromLocalFile(filePath));
        // Emitir señal al puente para notificar a la interfaz de React
        emit m_bridge->fileLoaded(filePath);
    }
}

void MainWindow::handleJSMessage(const QString &message)
{
    qInfo() << "MainWindow: Recibido mensaje desde JS:" << message;
    statusBar()->showMessage(tr("Mensaje recibido de JS: %1").arg(message), 5000);
}
