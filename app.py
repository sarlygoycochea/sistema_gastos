from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3

app = Flask(__name__)
app.secret_key = "clave_secreta"

def conectar():
    conexion = sqlite3.connect("gastos.db")
    conexion.row_factory = sqlite3.Row
    return conexion

def crear_tabla():
    conexion = conectar()
    conexion.execute("""
        CREATE TABLE IF NOT EXISTS gastos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            monto REAL NOT NULL
        )
    """)
    conexion.commit()
    conexion.close()

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form["usuario"]
        clave = request.form["clave"]

        if usuario == "admin" and clave == "123":
            session["usuario"] = usuario
            return redirect(url_for("inicio"))

        flash("Usuario o contraseña incorrectos")

    return render_template("login.html")

@app.route("/inicio")
def inicio():
    if "usuario" not in session:
        return redirect(url_for("login"))

    conexion = conectar()
    gastos = conexion.execute(
        "SELECT * FROM gastos ORDER BY fecha DESC"
    ).fetchall()

    total = conexion.execute(
        "SELECT SUM(monto) FROM gastos"
    ).fetchone()[0]

    conexion.close()

    return render_template(
        "inicio.html", gastos=gastos, total=total or 0
    )

@app.route("/registrar", methods=["POST"])
def registrar():
    if "usuario" not in session:
        return redirect(url_for("login"))

    fecha = request.form["fecha"]
    descripcion = request.form["descripcion"]
    monto = float(request.form["monto"])

    if monto <= 0 or not descripcion.strip():
        return redirect(url_for("inicio"))

    conexion = conectar()
    conexion.execute(
        "INSERT INTO gastos (fecha, descripcion, monto) VALUES (?, ?, ?)",
        (fecha, descripcion, monto)
    )
    conexion.commit()
    conexion.close()

    return redirect(url_for("inicio"))

@app.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
    if "usuario" not in session:
        return redirect(url_for("login"))

    conexion = conectar()

    gasto = conexion.execute(
        "SELECT * FROM gastos WHERE id = ?", (id,)
    ).fetchone()

    if gasto is None:
        conexion.close()
        return redirect(url_for("inicio"))

    if request.method == "POST":
        fecha = request.form["fecha"]
        descripcion = request.form["descripcion"]
        monto = float(request.form["monto"])

        if fecha and descripcion.strip() and monto > 0:
            conexion.execute("""
                UPDATE gastos
                SET fecha = ?, descripcion = ?, monto = ?
                WHERE id = ?
            """, (fecha, descripcion, monto, id))

            conexion.commit()
            conexion.close()
            return redirect(url_for("inicio"))

    conexion.close()
    return render_template("editar.html", gasto=gasto)

@app.route("/eliminar/<int:id>", methods=["POST"])
def eliminar(id):
    if "usuario" not in session:
        return redirect(url_for("login"))

    conexion = conectar()
    conexion.execute(
        "DELETE FROM gastos WHERE id = ?", (id,)
    )
    conexion.commit()
    conexion.close()

    return redirect(url_for("inicio"))

@app.route("/salir")
def salir():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    crear_tabla()
    app.run(debug=True)