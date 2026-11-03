from flask import request, current_app

def is_internal_request() -> bool:
    """
    Определяет, относится ли входящий HTTP-запрос к внутренней части для сотрудников.
    Внутренняя часть открывается по адресу http://contractmaker.umcgochs.local
    (Apache проксирует запросы на это же приложение Flask).
    """
    # 1. Проверка явного маркера от Apache VirtualHost (RequestHeader set X-Site "internal")
    site_hdr = (request.headers.get("X-Site") or "").strip().lower()
    if site_hdr in ("internal", "staff"):
        return True
    if site_hdr in ("public", "external"):
        return False

    # 2. Проверка домена / хоста в заголовках Host, X-Forwarded-Host и SERVER_NAME
    internal_hosts = set(
        h.strip().lower()
        for h in current_app.config.get("INTERNAL_HOSTS", ["contractmaker.umcgochs.local", "contractmaker.local"])
        if h.strip()
    )

    candidates = [
        request.headers.get("X-Forwarded-Host"),
        request.headers.get("X-Forwarded-Server"),
        request.host,
        request.environ.get("HTTP_HOST"),
        request.environ.get("SERVER_NAME"),
    ]

    for cand in candidates:
        if cand:
            host_only = cand.split(":")[0].strip().lower()
            if host_only in internal_hosts:
                return True

    # 3. Режим локальной разработки и тестирования (localhost / 127.0.0.1 / testserver)
    # Позволяет разработчикам комфортно тестировать внутренний раздел без обязательного изменения hosts
    if current_app.config.get("ALLOW_DEV_INTERNAL_ACCESS", True) and (current_app.debug or current_app.testing):
        if request.args.get("site") == "internal" or request.cookies.get("site") == "internal":
            return True
        dev_hosts = {"127.0.0.1", "localhost", "testserver"}
        current_host = (request.host or "").split(":")[0].strip().lower()
        if current_host in dev_hosts:
            return True

    return False
