import logging
from dotenv import load_dotenv
import uvicorn
import ssl
from os import environ

def run () -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    load_dotenv()

    uvicorn_config = {
        "app": "src.main:app",
        "host": "0.0.0.0",
        "port": int(environ["PORT"]),
        "log_level": "info",
        "reload": environ.get("STAGE") != "prod",
    }

    ssl_keyfile = environ.get("SSL_KEYFILE")
    ssl_certfile = environ.get("SSL_CERTFILE")

    if ssl_keyfile and ssl_certfile:
        uvicorn_config.update({
            "ssl_version": ssl.PROTOCOL_TLS,
            "ssl_keyfile": ssl_keyfile,
            "ssl_certfile": ssl_certfile
        })

    uvicorn.run(**uvicorn_config)

if __name__ == "__main__":
    run()
