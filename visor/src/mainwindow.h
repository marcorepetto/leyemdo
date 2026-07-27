#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <KParts/MainWindow>

namespace KParts {
    class ReadOnlyPart;
}

class QTabWidget;
class QWebEngineView;
class QWebChannel;
class JSBridge;

class MainWindow : public KParts::MainWindow
{
    Q_OBJECT

public:
    explicit MainWindow(QWidget *parent = nullptr);
    ~MainWindow() override;

    void openDocument(const QString &filePath);

private slots:
    void handleJSMessage(const QString &message);
    void scrollToPage(int pageNumber);
    void setCurrentTab(int tabIndex);

private:
    void setupVisor();
    void setupShortcuts();
    void handleShortcutTriggered(const QString &actionType);

    KParts::ReadOnlyPart *m_part;
    QTabWidget *m_tabWidget;
    QWebEngineView *m_chatView;
    QWebEngineView *m_libraryView;
    QWebChannel *m_channel;
    JSBridge *m_bridge;
    QString m_currentFilePath;
};

#endif // MAINWINDOW_H
