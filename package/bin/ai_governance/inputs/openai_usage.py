"""OpenAI aggregated usage and cost input."""

from __future__ import annotations

import time

from splunklib import modularinput as smi

from ai_governance import PROVIDER_OPENAI, ST_OPENAI_COST, ST_OPENAI_USAGE
from ai_governance.account import get_account_config, require_fields, require_provider
from ai_governance.checkpoint import CheckpointStore
from ai_governance.events import envelope
from ai_governance.inputs.base import run_input, stanza_key
from ai_governance.input_utils import parse_bool, parse_int, write_json_event
from ai_governance.providers.openai_api import OpenAIAPI


def validate_input(definition: smi.ValidationDefinition) -> None:
    return


def stream_events(inputs: smi.InputDefinition, event_writer: smi.EventWriter) -> None:
    run_input(
        inputs,
        event_writer,
        input_type="openai_usage",
        collect=_collect,
        sourcetype=ST_OPENAI_USAGE,
    )


def _flatten_buckets(buckets):
    """Usage endpoints return time buckets each containing results[]."""
    for bucket in buckets:
        start = bucket.get("start_time")
        end = bucket.get("end_time")
        for result in bucket.get("results", []) or []:
            item = dict(result)
            item["bucket_start_time"] = start
            item["bucket_end_time"] = end
            yield item


def _collect(logger, session_key, input_key, input_item, event_writer) -> int:
    account_name = input_item.get("account")
    account = get_account_config(session_key, account_name)
    require_provider(account, PROVIDER_OPENAI)
    require_fields(account, "openai_admin_key")

    api = OpenAIAPI(
        admin_key=account["openai_admin_key"], proxy_url=account.get("proxy_url")
    )
    checkpoint = CheckpointStore(session_key)
    ckpt_key = stanza_key(input_key)

    lookback_days = min(parse_int(input_item.get("lookback_days"), 7), 90)
    bucket_width = input_item.get("bucket_width") or "1d"
    if bucket_width not in ("1h", "1d"):
        bucket_width = "1d"
    index = input_item.get("index")

    now = int(time.time())
    start_time = now - lookback_days * 86400
    count = 0

    if parse_bool(input_item.get("collect_usage"), True):
        try:
            for item in _flatten_buckets(
                api.usage_completions(start_time, bucket_width=bucket_width)
            ):
                payload = envelope(
                    item, provider=PROVIDER_OPENAI, category="usage"
                )
                write_json_event(
                    event_writer=event_writer,
                    payload=payload,
                    index=index,
                    sourcetype=ST_OPENAI_USAGE,
                    source="aigov:openai:usage:%s" % account_name,
                    event_time=item.get("bucket_start_time"),
                )
                count += 1
        except Exception as exc:
            logger.warning("OpenAI usage collection failed: %s", exc)

    if parse_bool(input_item.get("collect_costs"), True):
        try:
            for item in _flatten_buckets(api.costs(start_time)):
                payload = envelope(item, provider=PROVIDER_OPENAI, category="cost")
                write_json_event(
                    event_writer=event_writer,
                    payload=payload,
                    index=index,
                    sourcetype=ST_OPENAI_COST,
                    source="aigov:openai:costs:%s" % account_name,
                    event_time=item.get("bucket_start_time"),
                )
                count += 1
        except Exception as exc:
            logger.warning("OpenAI cost collection failed: %s", exc)

    checkpoint.update(ckpt_key, last_run_epoch=now)
    logger.info("Ingested %s OpenAI usage/cost records", count)
    return count
