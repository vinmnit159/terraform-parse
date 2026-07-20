"""Terraform-Parse service: POST a payload, validate properties and  get back a rendered tf file
"""

import json
import logging
import os
from pathlib import Path

from flask import Flask, jsonify, request

from renderer import render_s3_tf
from validators import ValidationError, validate_payload

OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", "output"))


class JsonFormatter(logging.Formatter):
    """Structured JSON logs so log aggregators can parse fields directly."""

    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "time": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            entry["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(entry)


def _configure_logging() -> logging.Logger:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logger = logging.getLogger("terraform-parse")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        logger.addHandler(handler)
    return logger


def create_app() -> Flask:
    app = Flask(__name__)
    logger = _configure_logging()

    @app.get("/healthz")
    def healthz():
        return jsonify(status="ok")

    @app.post("/api/v1/render")
    def render():
        body = request.get_json(silent=True)
        if body is None:
            return jsonify(error="request must have a valid JSON body"), 400

        try:
            region, acl, bucket_name = validate_payload(body)
        except ValidationError as exc:
            logger.info("rejected payload: %s", exc)
            return jsonify(error=str(exc)), 400

        terraform = render_s3_tf(region, acl, bucket_name)
        filename = f"{bucket_name}.tf"

        try:
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            (OUTPUT_DIR / filename).write_text(terraform)
        except OSError:
            logger.exception("failed to write %s", filename)
            return jsonify(error="failed to persist terraform file"), 500

        logger.info(
            "rendered %s (region=%s acl=%s)", filename, region, acl
        )
        return jsonify(filename=filename, terraform=terraform), 201

    @app.errorhandler(404)
    def not_found(_exc):
        return jsonify(error="not found"), 404

    @app.errorhandler(405)
    def method_not_allowed(_exc):
        return jsonify(error="method not allowed"), 405

    @app.errorhandler(500)
    def internal_error(_exc):
        logger.exception("unhandled error")
        return jsonify(error="internal server error"), 500

    return app


app = create_app()