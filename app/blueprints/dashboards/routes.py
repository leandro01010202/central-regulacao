from flask import redirect, url_for, render_template
from flask_login import current_user, login_required

from . import dashboards_bp


@dashboards_bp.route("/")
@login_required
def home():
    role = current_user.role
    if role == "recepcao":
        return redirect(url_for("reception.listar_pedidos"))
    if role == "malote":
        return redirect(url_for("malote.listar"))
    if role == "medico_regulador":
        return redirect(url_for("regulator.painel", tipo="municipal"))
    if role == "agendador_municipal":
        return redirect(url_for("scheduling.lista", tipo="municipal"))
    if role == "agendador_estadual":
        return redirect(url_for("scheduling.lista", tipo="estadual"))
    return render_template("dashboards/home.html")