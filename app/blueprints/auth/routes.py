from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user

from app.models.usuario import Usuario
from app.repositories import usuarios as usuarios_repo
from app.utils.security import verify_password
from . import auth_bp


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboards.home"))

    if request.method == "POST":
        cpf = request.form.get("cpf", "")
        senha = request.form.get("senha", "")

        usuario_db = usuarios_repo.obter_por_cpf(cpf)
        if not usuario_db:
            flash("CPF não encontrado ou usuário inativo.", "danger")
            return render_template("auth/login.html")

        if not verify_password(senha, usuario_db["senha_hash"]):
            flash("Senha inválida.", "danger")
            return render_template("auth/login.html")

        usuario = Usuario.from_row(usuario_db)
        login_user(usuario)
        flash("Login realizado com sucesso.", "success")
        return redirect(url_for("dashboards.home"))

    return render_template("auth/login.html")


@auth_bp.route("/logout")
def logout():
    if current_user.is_authenticated:
        logout_user()
    flash("Sessão encerrada.", "info")
    return redirect(url_for("auth.login"))