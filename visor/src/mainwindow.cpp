#include "mainwindow.h"
#include <KParts/PartLoader>
#include <KParts/ReadOnlyPart>
#include <QHBoxLayout>
#include <QMessageBox>
#include <QDebug>

MainWindow::MainWindow(QWidget *parent)
    : KXmlGuiWindow(parent)
    , m_part(nullptr)
{
    setupVisor();
}

MainWindow::~MainWindow()
{
}

void MainWindow::setupVisor()
{
    // Crear el widget central
    QWidget *centralWidget = new QWidget(this);
    setCentralWidget(centralWidget);

    QHBoxLayout *layout = new QHBoxLayout(centralWidget);
    layout->setContentsMargins(0, 0, 0, 0);

    // Cargar la parte de Okular dinámicamente para el MimeType de PDF
    auto result = KParts::PartLoader::instantiatePartForMimeType<KParts::ReadOnlyPart>(
        QStringLiteral("application/pdf"), centralWidget, this
    );

    if (result) {
        m_part = result.plugin;
        layout->addWidget(m_part->widget());

        // Inicializar la GUI básica de la ventana principal y fusionar el KPart
        setupGUI(ToolBar | MenuBar | StatusBar);
        createGUI(m_part);
        
        // Configurar título por defecto
        setWindowTitle(tr("Lector PDF Inteligente"));
        resize(1024, 768);
    } else {
        qCritical() << "No se pudo cargar el KPart de Okular para PDF:" << result.errorText;
        QMessageBox::critical(this, tr("Error de Carga"),
            tr("No se pudo encontrar o cargar el plugin de visor de PDF de Okular. "
               "Asegúrate de tener instalado el paquete 'okular-part'.\nDetalle: ") + result.errorText);
    }
}

void MainWindow::openDocument(const QString &filePath)
{
    if (m_part && !filePath.isEmpty()) {
        m_part->openUrl(QUrl::fromLocalFile(filePath));
    }
}
