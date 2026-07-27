#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <KParts/MainWindow>

namespace KParts {
    class ReadOnlyPart;
}

class MainWindow : public KParts::MainWindow
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
