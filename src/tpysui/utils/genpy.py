#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Python source generation."""

import ast
from typing import cast
from pysui import PysuiConfiguration

from ..modals import GenSpec

_HEADER_TXT = """#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-\n
"""


_MAIN_ASYNC_TAIL: str = """ 
if __name__ == \"__main__\":
    asyncio.run(main())
"""


_MAIN_ASYNC_TEXT: str = """ 
async def main_loop():
    \"""Main async execution point.\"""
"""

_MAIN_ASYNC_INIT_TEXT: str = """ 
def main():
    \"""Main entry point.\"""
    asyncio.run(main_loop())
"""

_MAIN_SYNC_TAIL: str = """ 
if __name__ == \"__main__\":
    main()
"""


def _for_async_main(protocol: str, cfg: PysuiConfiguration) -> str:
    """Generate asynchronous usage

    Args:
        protocol (str): Indicates GraphQL or gRPC
        cfg (PysuiConfiguration): The active configuration

    Returns:
        str: the ast parsed function blocks
    """
    ast_func: ast.AsyncFunctionDef = ast.parse(_MAIN_ASYNC_TEXT).body[0]
    ast_main: ast.FunctionDef = ast.parse(_MAIN_ASYNC_INIT_TEXT).body[0]
    ast_init: ast.FunctionDef = ast.parse(_MAIN_SYNC_TAIL).body[0]
    ast_func.body.append(
        ast.parse(
            f'cfg=PysuiConfiguration(from_cfg_path="{cfg.config}", group_name="{cfg.active_group_name}")'
        ).body[0]
    )
    use_client = "AsyncGqlClient" if protocol == "GraphQL" else "SuiGrpcClient"
    ast_func.body.append(ast.parse(f"client={use_client}(pysui_config=cfg)").body[0])
    return f"\n\n{ast.unparse(ast_func)}\n\n{ast.unparse(ast_main)}\n\n{ast.unparse(ast_init)}"


_MAIN_SYNC_TEXT: str = """ 
def main():
    \"""Main sync entry point.\"""
"""


def _for_sync_main(cfg: PysuiConfiguration) -> str:
    """Generate synchronous (GraphQL) usage

    Args:
        cfg (PysuiConfiguration): The active configuration

    Returns:
        str: the ast parsed function blocks
    """
    ast_func = cast(ast.FunctionDef, ast.parse(_MAIN_SYNC_TEXT).body[0])
    ast_init: ast.FunctionDef = ast.parse(_MAIN_SYNC_TAIL).body[0]
    ast_func.body.append(
        ast.parse(
            f'cfg=PysuiConfiguration(from_cfg_path="{cfg.config}", group_name="{cfg.active_group_name}")'
        ).body[0]
    )
    ast_func.body.append(ast.parse("client=SyncGqlClient(pysui_config=cfg)").body[0])
    return f"\n\n{ast.unparse(ast_func)}\n\n{ast.unparse(ast_init)}"


def _for_grpc(astmod: ast.Module) -> None:
    """Generate gRPC include.

    Args:
        astmod (ast.Module): main ast module
    """
    astmod.body.append(ast.parse("from pysui import SuiGrpcClient").body[0])


def _for_gql(astmod: ast.Module, async_flag: bool) -> None:
    """Generate GraphQL includes

    Args:
        astmod (ast.Module): main ast module
        async_flag (bool): whether using async or sync
    """
    if async_flag:
        astmod.body.append(ast.parse("from pysui import AsyncGqlClient").body[0])
    else:
        astmod.body.append(ast.parse("from pysui import SyncGqlClient").body[0])


def generate_python(*, gen_spec: GenSpec, from_config: PysuiConfiguration) -> None:
    """generate_python _summary_

    Args:
        gen_spec (GenSpec): The code generation specification
        from_config (PysuiConfiguraiton): Current configuration
    """
    file_path = gen_spec.fpath.expanduser()
    file_parent = file_path.parent
    if file_path.exists() and not gen_spec.force:
        raise ValueError(f"{file_path.name} already exists. Use 'force' to overwrite.")
    if not file_parent.exists():
        file_parent.mkdir(parents=True, exist_ok=True)

    astmain = ast.parse(f'"""Generated {file_path.name} from tpysui."""')
    if gen_spec.async_protocol:
        astmain.body.append(ast.parse("import asyncio").body[0])

    astmain.body.append(ast.parse("from pysui import PysuiConfiguration").body[0])

    if gen_spec.client_type == "GraphQL":
        _for_gql(astmain, gen_spec.async_protocol)
    else:
        _for_grpc(astmain)

    if gen_spec.async_protocol:
        main_text = _for_async_main(gen_spec.client_type, from_config)
    else:
        main_text = _for_sync_main(from_config)

    text = f"{_HEADER_TXT}\n{ast.unparse(astmain)}\n{main_text}\n"
    file_path.write_text(text, encoding="utf8")
