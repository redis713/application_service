from flask import render_template, redirect, url_for, request, current_app
from app.blueprints.main import main_bp

@main_bp.route("/")
def index():
    # Если обращение происходит по внутреннему домену (contractmaker.umcgochs.local)
    # или с маркером X-Site: internal, сразу открываем реестр заявок для сотрудников
    raw_host = (request.headers.get("X-Forwarded-Host") or request.host or "").split(":")[0].strip().lower()
    internal_hosts = set(
        h.strip().lower()
        for h in current_app.config.get("INTERNAL_HOSTS", ["contractmaker.umcgochs.local", "contractmaker.local"])
        if h.strip()
    )
    if raw_host in internal_hosts or request.headers.get("X-Site") == "internal" or request.args.get("site") == "internal":
        return redirect(url_for("internal.applications_list"))

    return render_template("main/index.html")

@main_bp.route("/distant")
def distant():
    return render_template("main/distant.html")

@main_bp.route("/ochno")
def ochno():
    return render_template("main/ochka.html")
