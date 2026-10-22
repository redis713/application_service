from app import create_app

app = create_app()

if __name__ == "__main__":
    # По умолчанию запускаем на 127.0.0.1 (локально, мгновенный старт без опроса сетевых адаптеров)
    app.run(host="127.0.0.1", port=5000, debug=True)

