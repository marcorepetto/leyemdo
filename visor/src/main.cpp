#include "mainwindow.h"
#include <QApplication>
#include <KAboutData>
#include <QCommandLineParser>
#include <QCommandLineOption>
#include <QDir>

int main(int argc, char *argv[])
{
    QApplication app(argc, argv);

    // Inicializar metadatos de la aplicación para que KDE KParts funcione correctamente
    KAboutData aboutData(
        QStringLiteral("lector-visor"),
        QObject::tr("Lector PDF Inteligente"),
        QStringLiteral("0.1.0"),
        QObject::tr("Visor nativo basado en Okular para el lector de PDF inteligente."),
        KAboutLicense::GPL,
        QObject::tr("(c) 2026 Grupo de Desarrollo")
    );
    
    aboutData.addAuthor(
        QObject::tr("Desarrollador"),
        QObject::tr("Autor Principal"),
        QStringLiteral("mrepetto@example.com")
    );

    KAboutData::setApplicationData(aboutData);

    // Analizador de línea de comandos para recibir el archivo PDF
    QCommandLineParser parser;
    aboutData.setupCommandLine(&parser);
    parser.addPositionalArgument(QStringLiteral("file"), QObject::tr("Documento PDF a abrir."));
    parser.process(app);
    aboutData.processCommandLine(&parser);

    MainWindow window;
    window.show();

    // Si se pasa un argumento, intentar abrir el archivo PDF
    const QStringList args = parser.positionalArguments();
    if (!args.isEmpty()) {
        QString filePath = args.at(0);
        // Resolver ruta absoluta si es relativa
        if (QDir::isRelativePath(filePath)) {
            filePath = QDir::current().absoluteFilePath(filePath);
        }
        window.openDocument(filePath);
    }

    return app.exec();
}
