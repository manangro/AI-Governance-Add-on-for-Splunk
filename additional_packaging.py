"""Post-build cleanup executed by ucc-gen.

Removes optional binary dependencies (grpcio, protobuf and the OTLP/gRPC
OpenTelemetry exporter chain) that solnlib only imports lazily when OTLP
metric export is explicitly requested - which this add-on never does.

These packages ship platform-specific x86_64 .so files that are not
AArch64-compatible and would fail AppInspect's aarch64 compatibility
check; the add-on itself is pure Python.
"""

import os
import shutil


def additional_packaging(ta_name: str) -> None:
    lib = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", ta_name, "lib")

    prune = [
        "grpc",
        "google",
        os.path.join("opentelemetry", "exporter"),
        os.path.join("opentelemetry", "proto"),
    ]
    prune_dist_info_prefixes = (
        "grpcio-",
        "protobuf-",
        "googleapis_common_protos-",
        "opentelemetry_exporter_otlp_proto_grpc-",
        "opentelemetry_exporter_otlp_proto_common-",
        "opentelemetry_proto-",
    )

    for relpath in prune:
        target = os.path.join(lib, relpath)
        if os.path.isdir(target):
            shutil.rmtree(target)
            print("additional_packaging: removed %s" % target)

    for entry in os.listdir(lib):
        if entry.startswith(prune_dist_info_prefixes):
            target = os.path.join(lib, entry)
            if os.path.isdir(target):
                shutil.rmtree(target)
                print("additional_packaging: removed %s" % target)

    # Remove any stray bytecode caches so AppInspect stays clean.
    for root, dirs, _files in os.walk(os.path.join(lib, os.pardir)):
        for d in list(dirs):
            if d == "__pycache__":
                shutil.rmtree(os.path.join(root, d))
                dirs.remove(d)
