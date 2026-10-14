from collections.abc import Generator, Iterable
from pathlib import Path

from gofra.cli.output import cli_message
from libgofra.driver.artifact import FrontendArtifact
from libgofra.driver.diagnostics import DiagnosticConsumer
from libgofra.driver.request import CompilationRequest
from libgofra.frontend.import_path_resolver import (
    try_resolve_and_find_real_include_path,
)
from libgofra.hir.module import Module
from libgofra.lexer import tokenize_from_raw
from libgofra.lexer.io import open_source_file_line_stream
from libgofra.lexer.tokens import Token
from libgofra.parser.parser import parse_module_from_tokenizer
from libgofra.preprocessor import preprocess_file
from libgofra.preprocessor.macros import registry_from_raw_definitions
from libgofra.preprocessor.macros.registry import MacrosRegistry


def driver_run_frontend_stage(
    request: CompilationRequest,
    diag: DiagnosticConsumer,
) -> FrontendArtifact:
    with diag.timer("Frontend (lexer + parser)"):
        macros = registry_from_raw_definitions(
            location=request.definitions_location,
            definitions=request.definitions,
        ).inject_propagated_defaults(target=request.target)

        module = load_module_graph(
            request.source_filepath,
            request.include_paths,
            macros=macros,
            rt_array_oob_check=request.runtime_array_oob_checks,
            entry_point_name=request.executable_entry_point,
        )

    # Display collected modules
    paths = module.flatten_dependencies_paths(include_self=True)
    names = ", ".join(str(p.relative_to(request.source_filepath.parent)) for p in paths)
    suffix = "" if len(paths) == 1 else "s"
    diag.info(f"Collected {len(paths)} module{suffix}: {names}")

    return FrontendArtifact(root=module)


def load_module_graph(
    filepath: Path,
    include_paths: Iterable[Path],
    *,
    macros: MacrosRegistry,
    rt_array_oob_check: bool = False,
    entry_point_name: str = "main",
) -> Module:
    """Compiles given filepath down to `IR` into `Module` (e.g translation unit).

    Requires compiling dependency modules (e.g returned_module.dependencies).
    """
    module = Module(path=filepath)

    def on_import_request(
        named_import_as_name: str,
        requested_import_path: Path,
    ) -> None:
        import_path = try_resolve_and_find_real_include_path(
            requested_import_path,
            current_path=Path(),
            search_paths=include_paths,
        )
        if import_path is None:
            msg = f"Cannot find import path for module '{requested_import_path}' at ..."
            raise ValueError(msg)

        already_imported_paths = (m.path for m in module.dependencies.values())
        if import_path in already_imported_paths:
            cli_message(
                "WARNING",
                "Tried to import already imported module -> rejecting",
            )
            return

        imported_module = load_module_graph(
            import_path,
            include_paths=include_paths,
            macros=macros.copy(),
            rt_array_oob_check=rt_array_oob_check,
            entry_point_name=entry_point_name,
        )
        assert named_import_as_name not in module.dependencies
        module.dependencies[named_import_as_name] = imported_module

    return parse_module_from_tokenizer(
        module,
        tokenizer=_get_tokenizer(filepath, include_paths, macros),
        rt_array_oob_check=rt_array_oob_check,
        entry_point_name=entry_point_name,
        on_import_request=on_import_request,
    )


def _get_tokenizer(
    filepath: Path,
    include_paths: Iterable[Path],
    macros: MacrosRegistry,
) -> Generator[Token]:
    io = open_source_file_line_stream(filepath)
    lexer = tokenize_from_raw(filepath, lines=io)
    return preprocess_file(
        filepath,
        lexer,
        include_paths,
        macros,
    )
