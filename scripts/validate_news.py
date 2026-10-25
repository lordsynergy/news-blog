#!/usr/bin/env python3
"""Validate the weekly digest before it is committed and published."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlparse


CATEGORIES = ("psychology", "chemistry", "biology")
REQUIRED_ITEM_FIELDS = ("title", "summary", "source", "url", "published_at")


class ValidationError(ValueError):
    pass


def parse_iso_date(value: object, field: str) -> date:
    if not isinstance(value, str):
        raise ValidationError(f"{field} must be a string in YYYY-MM-DD format")
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ValidationError(f"{field} must use YYYY-MM-DD format") from error


def validate_item(item: object, category: str, index: int) -> str:
    path = f"categories.{category}[{index}]"
    if not isinstance(item, dict):
        raise ValidationError(f"{path} must be an object")

    for field in REQUIRED_ITEM_FIELDS:
        value = item.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(f"{path}.{field} must be a non-empty string")

    title = item["title"].strip()
    summary = item["summary"].strip()
    if len(title) > 180:
        raise ValidationError(f"{path}.title is longer than 180 characters")
    if not 120 <= len(summary) <= 900:
        raise ValidationError(f"{path}.summary must contain 120–900 characters")

    parsed_url = urlparse(item["url"].strip())
    if parsed_url.scheme != "https" or not parsed_url.netloc:
        raise ValidationError(f"{path}.url must be an absolute HTTPS URL")

    published = parse_iso_date(item["published_at"], f"{path}.published_at")
    if published > date.today():
        raise ValidationError(f"{path}.published_at cannot be in the future")

    return item["url"].strip().lower().rstrip("/")


def validate_digest(data: object, *, require_current: bool = True) -> None:
    if not isinstance(data, dict):
        raise ValidationError("document root must be an object")

    updated_at = parse_iso_date(data.get("updated_at"), "updated_at")
    if require_current and abs((date.today() - updated_at).days) > 1:
        raise ValidationError("updated_at must be today (a one-day timezone tolerance is allowed)")

    generated_at = data.get("generated_at")
    if not isinstance(generated_at, str):
        raise ValidationError("generated_at must be an ISO 8601 string")
    try:
        datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValidationError("generated_at must be a valid ISO 8601 timestamp") from error

    categories = data.get("categories")
    if not isinstance(categories, dict):
        raise ValidationError("categories must be an object")
    if set(categories) != set(CATEGORIES):
        raise ValidationError(f"categories must contain exactly: {', '.join(CATEGORIES)}")

    urls: set[str] = set()
    for category in CATEGORIES:
        items = categories[category]
        if not isinstance(items, list) or len(items) != 5:
            raise ValidationError(f"categories.{category} must contain exactly 5 items")
        for index, item in enumerate(items):
            normalized_url = validate_item(item, category, index)
            if normalized_url in urls:
                raise ValidationError(f"duplicate URL: {item['url']}")
            urls.add(normalized_url)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--allow-stale",
        action="store_true",
        help="accept an older updated_at value when validating an archive candidate",
    )
    parser.add_argument("path", nargs="?", default="data/news.json")
    args = parser.parse_args()
    path = Path(args.path)

    try:
        with path.open(encoding="utf-8") as file:
            data = json.load(file)
        validate_digest(data, require_current=not args.allow_stale)
    except (OSError, json.JSONDecodeError, ValidationError) as error:
        print(f"News validation failed: {error}", file=sys.stderr)
        return 1

    print(f"News validation passed: 15 unique items in {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
