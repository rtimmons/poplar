import os
import pkg_resources
import grpc_tools
import grpc_tools.protoc
import grpc

# pylint: disable=too-many-instance-attributes,too-many-statements,too-many-locals
def run_protoc():
    """Start up the jasper process manager."""
    root_dir = os.path.dirname(os.path.abspath(__file__))
    proto_file = os.path.join(root_dir,  "metrics.proto")
    try:
        well_known_protos_include = pkg_resources.resource_filename("grpc_tools", "_proto")
    except ImportError:
        raise ImportError("You must run: sys.executable + '-m pip install grpcio grpcio-tools "
                          "googleapis-common-protos' to use --spawnUsing=jasper.")

    # We use the build/ directory as the output directory because the generated files aren't
    # meant to because tracked by git or linted.
    proto_out = os.path.join(root_dir, "client")

    # utils.rmtree(proto_out, ignore_errors=True)
    os.makedirs(proto_out)

    # We make 'proto_out' into a Python package so we can add it to 'sys.path' and import the
    # *pb2*.py modules from it.
    with open(os.path.join(proto_out, "__init__.py"), "w"):
        pass

    ret = grpc_tools.protoc.main([
        grpc_tools.protoc.__file__,
        "--grpc_python_out",
        proto_out,
        "--python_out",
        proto_out,
        "--proto_path",
        os.path.dirname(proto_file),
        "--proto_path",
        well_known_protos_include,
        os.path.basename(proto_file),
    ])

    if ret != 0:
        raise RuntimeError("Failed to generated gRPC files from the jasper.proto file")

run_protoc()
