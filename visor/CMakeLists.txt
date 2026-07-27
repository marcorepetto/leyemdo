cmake_minimum_required(VERSION 3.16)
project(lector-visor VERSION 0.1.0)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTOUIC ON)
set(CMAKE_AUTORCC ON)

# Buscar Dependencias
find_package(Qt6 COMPONENTS Widgets Core REQUIRED)
find_package(KF6 COMPONENTS Parts XmlGui I18n REQUIRED)
find_package(Okular6 REQUIRED)

# Agregar Ejecutable
add_executable(lector-visor
    src/main.cpp
    src/mainwindow.h
    src/mainwindow.cpp
)

# Enlazar Bibliotecas
target_link_libraries(lector-visor
    PRIVATE
    Qt6::Widgets
    Qt6::Core
    KF6::Parts
    KF6::XmlGui
    KF6::I18n
    Okular6
)
