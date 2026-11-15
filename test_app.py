import sqlite3
import pytest
import app as sistema


@pytest.fixture
def cliente(tmp_path, monkeypatch):
    ruta = tmp_path / "pruebas.db"

    def conectar_prueba():
        conexion = sqlite3.connect(ruta)
        conexion.row_factory = sqlite3.Row
        return conexion

    monkeypatch.setattr(sistema, "conectar", conectar_prueba)

    sistema.crear_tabla()
    sistema.app.config["TESTING"] = True

    with sistema.app.test_client() as cliente:
        yield cliente


def iniciar_sesion(cliente):
    return cliente.post("/", data={
        "usuario": "admin",
        "clave": "123"
    })


def test_pagina_login(cliente):
    respuesta = cliente.get("/")
    assert respuesta.status_code == 200


def test_login_correcto(cliente):
    respuesta = iniciar_sesion(cliente)
    assert respuesta.status_code == 302
    assert respuesta.location.endswith("/inicio")


def test_acceso_sin_sesion(cliente):
    respuesta = cliente.get("/inicio")
    assert respuesta.status_code == 302


def test_registrar_gasto(cliente):
    iniciar_sesion(cliente)

    respuesta = cliente.post("/registrar", data={
        "fecha": "2026-11-14",
        "descripcion": "Alimentos",
        "monto": "25.50"
    })

    assert respuesta.status_code == 302

    conexion = sistema.conectar()
    gasto = conexion.execute(
        "SELECT * FROM gastos"
    ).fetchone()
    conexion.close()

    assert gasto["descripcion"] == "Alimentos"
    assert gasto["monto"] == 25.50


def test_editar_gasto(cliente):
    iniciar_sesion(cliente)

    cliente.post("/registrar", data={
        "fecha": "2026-11-14",
        "descripcion": "Alimentos",
        "monto": "25.50"
    })

    conexion = sistema.conectar()
    gasto = conexion.execute(
        "SELECT id FROM gastos"
    ).fetchone()
    conexion.close()

    respuesta = cliente.post(
        f"/editar/{gasto['id']}",
        data={
            "fecha": "2026-11-15",
            "descripcion": "Compras",
            "monto": "40.00"
        }
    )

    assert respuesta.status_code == 302

    conexion = sistema.conectar()
    actualizado = conexion.execute(
        "SELECT * FROM gastos"
    ).fetchone()
    conexion.close()

    assert actualizado["descripcion"] == "Compras"
    assert actualizado["monto"] == 40.00


def test_eliminar_gasto(cliente):
    iniciar_sesion(cliente)

    cliente.post("/registrar", data={
        "fecha": "2026-11-14",
        "descripcion": "Pasajes",
        "monto": "8.00"
    })

    conexion = sistema.conectar()
    gasto = conexion.execute(
        "SELECT id FROM gastos"
    ).fetchone()
    conexion.close()

    respuesta = cliente.post(
        f"/eliminar/{gasto['id']}"
    )

    assert respuesta.status_code == 302

    conexion = sistema.conectar()
    cantidad = conexion.execute(
        "SELECT COUNT(*) FROM gastos"
    ).fetchone()[0]
    conexion.close()

    assert cantidad == 0


def test_total_acumulado(cliente):
    iniciar_sesion(cliente)

    cliente.post("/registrar", data={
        "fecha": "2026-11-14",
        "descripcion": "Alimentos",
        "monto": "25.50"
    })

    cliente.post("/registrar", data={
        "fecha": "2026-11-14",
        "descripcion": "Pasajes",
        "monto": "8.00"
    })

    respuesta = cliente.get("/inicio")

    assert respuesta.status_code == 200
    assert b"33.50" in respuesta.data