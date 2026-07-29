"""Analytics reports input handler."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict

from solnlib import log
from splunklib import modularinput as smi

from ta_anthropic_claude_enterprise.analytics_dates import resolve_analytics_start_date
from ta_anthropic_claude_enterprise.account import build_client_from_account
from ta_anthropic_claude_enterprise.api.analytics import AnalyticsAPI
from ta_anthropic_claude_enterprise.api.spend_limits import SpendLimitsAPI
from ta_anthropic_claude_enterprise.checkpoint import CheckpointStore
from ta_anthropic_claude_enterprise.constants import (
    SOURCETYPE_ANALYTICS_COST,
    SOURCETYPE_ANALYTICS_SPEND_LIMIT,
    SOURCETYPE_ANALYTICS_SPEND_LIMIT_REQUEST,
    SOURCETYPE_ANALYTICS_SUMMARY,
    SOURCETYPE_ANALYTICS_USAGE,
    SOURCETYPE_ANALYTICS_USER_ACTIVITY,
    SOURCETYPE_ANALYTICS_USER_COST,
    SOURCETYPE_ANALYTICS_USER_USAGE,
)
from ta_anthropic_claude_enterprise.events import (
    wrap_analytics_record,
    wrap_spend_limit_record,
)
from ta_anthropic_claude_enterprise.input_utils import (
    configure_logger,
    logger_for_input,
    parse_bool,
    parse_int,
    write_json_event,
)


# Bump when collection output changes shape enough that already-indexed
# events are wrong or incomplete (2 = per-user reports grouped by
# model/product with per-day user activity; 3 = grouped reports requested
# in bounded windows so large backfills keep model/product attribution).
# A checkpoint stamped with an older version is discarded once so history
# is re-collected.
COLLECTION_SCHEMA_VERSION = 3


def _window_chunks(start_date: date, end_date: date, days: int):
    """Split [start_date, end_date) into consecutive windows of at most
    `days` days."""
    windows = []
    cursor = start_date
    while cursor < end_date:
        upper = min(cursor + timedelta(days=days), end_date)
        windows.append((cursor, upper))
        cursor = upper
    return windows


def _day_to_rfc3339(day: date) -> str:
    return datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def validate_input(definition: smi.ValidationDefinition) -> None:
    return


def stream_events(inputs: smi.InputDefinition, event_writer: smi.EventWriter) -> None:
    for input_name, input_item in inputs.inputs.items():
        normalized_input_name = input_name.split("/")[-1]
        logger = logger_for_input(normalized_input_name)
        session_key = inputs.metadata["session_key"]
        configure_logger(logger, session_key)
        log.modular_input_start(logger, normalized_input_name)

        try:
            counts = _collect_analytics(
                logger=logger,
                session_key=session_key,
                input_key=input_name,
                input_item=input_item,
                event_writer=event_writer,
            )
            for sourcetype, count in counts.items():
                if count:
                    log.events_ingested(
                        logger,
                        input_name,
                        sourcetype,
                        count,
                        input_item.get("index"),
                        account=input_item.get("account"),
                    )
            log.modular_input_end(logger, normalized_input_name)
        except Exception as exc:
            log.log_exception(
                logger,
                exc,
                "analytics_reports_error",
                msg_before="Failed to collect analytics reports: ",
            )


def _collect_analytics(
    logger,
    session_key: str,
    input_key: str,
    input_item: Dict[str, Any],
    event_writer: smi.EventWriter,
) -> Dict[str, int]:
    account_name = input_item.get("account")
    client = build_client_from_account(
        session_key, account_name, require_analytics=True
    )
    analytics = AnalyticsAPI(client)
    checkpoint = CheckpointStore(session_key)
    state = checkpoint.get(input_key)

    index = input_item.get("index")
    bucket_width = input_item.get("bucket_width") or "1d"
    source_prefix = f"anthropic:analytics:{account_name}"

    end_date = AnalyticsAPI.latest_finalized_date()
    backfill_days = min(parse_int(input_item.get("backfill_days"), 7), 90)
    if state and state.get("schema_version") != COLLECTION_SCHEMA_VERSION:
        logger.info(
            "Analytics collection schema upgraded (adds per-user model/product "
            "attribution); re-collecting the last 90 days to replace "
            "unattributed history"
        )
        state = {}
        backfill_days = 90
    start_date = resolve_analytics_start_date(state, end_date, backfill_days)
    # Long grouped report windows can be rejected with a 400; request the
    # reports in bounded chunks so grouping (model/product attribution)
    # survives large backfills.
    report_windows = _window_chunks(start_date, end_date, days=30)

    counts: Dict[str, int] = {
        SOURCETYPE_ANALYTICS_SUMMARY: 0,
        SOURCETYPE_ANALYTICS_USAGE: 0,
        SOURCETYPE_ANALYTICS_COST: 0,
        SOURCETYPE_ANALYTICS_USER_USAGE: 0,
        SOURCETYPE_ANALYTICS_USER_COST: 0,
        SOURCETYPE_ANALYTICS_USER_ACTIVITY: 0,
        SOURCETYPE_ANALYTICS_SPEND_LIMIT: 0,
        SOURCETYPE_ANALYTICS_SPEND_LIMIT_REQUEST: 0,
    }

    if parse_bool(input_item.get("collect_summaries"), True):
        counts[SOURCETYPE_ANALYTICS_SUMMARY] = _emit_summaries(
            analytics, start_date, end_date, event_writer, index, source_prefix
        )

    group_by = ["product", "model"]
    report_specs = [
        (
            "collect_usage",
            analytics.get_usage_report,
            "usage",
            SOURCETYPE_ANALYTICS_USAGE,
        ),
        ("collect_cost", analytics.get_cost_report, "cost", SOURCETYPE_ANALYTICS_COST),
        (
            "collect_user_usage",
            analytics.get_user_usage_report,
            "user_usage",
            SOURCETYPE_ANALYTICS_USER_USAGE,
        ),
        (
            "collect_user_cost",
            analytics.get_user_cost_report,
            "user_cost",
            SOURCETYPE_ANALYTICS_USER_COST,
        ),
    ]
    for setting, fetch, report_type, sourcetype in report_specs:
        if not parse_bool(input_item.get(setting), True):
            continue
        for window_start, window_end in report_windows:
            window_starting_at = _day_to_rfc3339(window_start)
            counts[sourcetype] += _emit_paginated_report(
                iterator=fetch(
                    starting_at=window_starting_at,
                    ending_at=_day_to_rfc3339(window_end),
                    bucket_width=bucket_width,
                    group_by=group_by,
                ),
                report_type=report_type,
                sourcetype=sourcetype,
                event_writer=event_writer,
                index=index,
                source=f"{source_prefix}:{report_type}",
                default_time=window_starting_at,
            )

    if parse_bool(input_item.get("collect_user_activity"), True):
        counts[SOURCETYPE_ANALYTICS_USER_ACTIVITY] = _emit_paginated_report(
            iterator=analytics.list_user_activity(
                starting_date=start_date, ending_date=end_date
            ),
            report_type="user_activity",
            sourcetype=SOURCETYPE_ANALYTICS_USER_ACTIVITY,
            event_writer=event_writer,
            index=index,
            source=f"{source_prefix}:user_activity",
        )

    if parse_bool(input_item.get("collect_spend_limits"), True):
        spend_limits = SpendLimitsAPI(client)
        counts[SOURCETYPE_ANALYTICS_SPEND_LIMIT] = _emit_spend_limit_report(
            iterator=spend_limits.list_effective_spend_limits(),
            record_type="spend_limit",
            sourcetype=SOURCETYPE_ANALYTICS_SPEND_LIMIT,
            event_writer=event_writer,
            index=index,
            source=f"{source_prefix}:spend_limits",
        )
        counts[SOURCETYPE_ANALYTICS_SPEND_LIMIT_REQUEST] = _emit_spend_limit_report(
            iterator=spend_limits.list_spend_limit_increase_requests(
                status=["pending"]
            ),
            record_type="spend_limit_request",
            sourcetype=SOURCETYPE_ANALYTICS_SPEND_LIMIT_REQUEST,
            event_writer=event_writer,
            index=index,
            source=f"{source_prefix}:spend_limit_requests",
        )

    if getattr(analytics, "last_group_by_fallback", None):
        logger.warning(
            "Analytics API rejected group_by; model/product attribution is "
            "unavailable and data was collected ungrouped: %s",
            analytics.last_group_by_fallback,
        )

    checkpoint.set(
        input_key,
        {
            "last_finalized_date": end_date.isoformat(),
            "schema_version": COLLECTION_SCHEMA_VERSION,
        },
    )
    logger.info("Analytics collection window %s to %s", start_date, end_date)
    return counts


def _emit_summaries(
    analytics: AnalyticsAPI,
    start_date: date,
    end_date: date,
    event_writer: smi.EventWriter,
    index: str,
    source_prefix: str,
) -> int:
    response = analytics.get_summaries(start_date, end_date)
    summaries = response.get("summaries", [])
    count = 0
    for summary in summaries:
        payload = wrap_analytics_record(summary, "summary")
        write_json_event(
            event_writer=event_writer,
            payload=payload,
            index=index,
            sourcetype=SOURCETYPE_ANALYTICS_SUMMARY,
            source=f"{source_prefix}:summary",
            event_time=summary.get("starting_at"),
        )
        count += 1
    return count


def _iter_flattened(records) -> "Any":
    """Flatten report buckets that wrap rows in a results[] array.

    The usage/cost report API returns one bucket per time window with the
    actual rows inside `results`. Emit one event per row, carrying the
    bucket-level fields (starting_at, ending_at, ...) onto each row so
    Splunk sees flat, searchable fields instead of results{}.* multivalues.
    """
    for record in records:
        results = record.get("results") if isinstance(record, dict) else None
        if not isinstance(results, list):
            yield record
            continue
        base = {k: v for k, v in record.items() if k != "results"}
        for result in results:
            if isinstance(result, dict):
                merged = dict(base)
                merged.update(result)
                yield merged


def _emit_paginated_report(
    iterator,
    report_type: str,
    sourcetype: str,
    event_writer: smi.EventWriter,
    index: str,
    source: str,
    default_time: str = None,
) -> int:
    count = 0
    for record in _iter_flattened(iterator):
        payload = wrap_analytics_record(record, report_type)
        write_json_event(
            event_writer=event_writer,
            payload=payload,
            index=index,
            sourcetype=sourcetype,
            source=source,
            event_time=record.get("starting_at")
            or record.get("date")
            or record.get("ending_at")
            or default_time,
        )
        count += 1
    return count


def _emit_spend_limit_report(
    iterator,
    record_type: str,
    sourcetype: str,
    event_writer: smi.EventWriter,
    index: str,
    source: str,
) -> int:
    count = 0
    snapshot_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for record in iterator:
        payload = wrap_spend_limit_record(record, record_type)
        write_json_event(
            event_writer=event_writer,
            payload=payload,
            index=index,
            sourcetype=sourcetype,
            source=source,
            event_time=snapshot_time,
        )
        count += 1
    return count
