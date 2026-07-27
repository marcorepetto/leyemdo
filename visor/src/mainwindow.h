#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <KXmlGuiWindow>

namespace KParts {
    class ReadOnlyPart;
}

class MainWindow : public KXmlGuiWindow
{
    Q_OBJECT

public:
    explicit MainWindow(QWidget *parent = nullptr);
    ~MainWindow() override;

    void openDocument(const QString &filePath);

private:
    void setupVisor();

    KParts::ReadOnlyPart *m_part;
};

#endif // MAINWINDOW_H
