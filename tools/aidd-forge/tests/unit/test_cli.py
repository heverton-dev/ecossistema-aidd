from pathlib import Path

import pytest

from aidd_forge.cli import build_parser, main


def test_build_parser_exposes_init_subcommand() -> None:
    parser = build_parser()
    args = parser.parse_args(["init", "some/path"])

    assert args.command == "init"
    assert args.path == "some/path"
    assert args.force is False


def test_init_default_path_is_current_dir() -> None:
    parser = build_parser()
    args = parser.parse_args(["init"])

    assert args.path == "."


def test_init_force_flag() -> None:
    parser = build_parser()
    args = parser.parse_args(["init", "--force"])

    assert args.force is True


def test_main_init_creates_governance_files(tmp_path: Path) -> None:
    exit_code = main(["init", str(tmp_path)])

    assert exit_code == 0
    assert (tmp_path / "governance" / "AGENTS.md").exists()
    assert (tmp_path / "CLAUDE.md").exists()


def test_main_init_is_idempotent_without_force(tmp_path: Path, capsys) -> None:
    main(["init", str(tmp_path)])
    capsys.readouterr()

    exit_code = main(["init", str(tmp_path)])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "arquivos criados: 0" in output


def test_build_parser_exposes_inject_subcommand() -> None:
    parser = build_parser()
    args = parser.parse_args(
        ["inject", "spec", "demo-spec", "--descricao", "Uma spec", "--conteudo", "Conteudo real."]
    )

    assert args.command == "inject"
    assert args.tipo == "spec"
    assert args.nome == "demo-spec"
    assert args.descricao == "Uma spec"
    assert args.conteudo == "Conteudo real."
    assert args.force is False


def test_inject_requires_conteudo_or_conteudo_file() -> None:
    parser = build_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(["inject", "spec", "demo-spec", "--descricao", "Uma spec"])


def test_inject_rejects_unknown_tipo() -> None:
    parser = build_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(["inject", "agent", "demo", "--descricao", "x", "--conteudo", "y"])


def test_main_inject_materializes_spec_file(tmp_path: Path, capsys) -> None:
    exit_code = main(
        [
            "inject",
            "spec",
            "demo-spec",
            "--descricao",
            "Uma spec de teste",
            "--conteudo",
            "Conteudo real da spec.\n",
            "--path",
            str(tmp_path),
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert (tmp_path / "docs" / "specs" / "demo-spec.md").read_text(encoding="utf-8") == (
        "Conteudo real da spec.\n"
    )
    assert "componente injetado: spec/demo-spec" in output


def test_main_inject_com_conteudo_file(tmp_path: Path) -> None:
    conteudo_path = tmp_path / "conteudo.md"
    conteudo_path.write_text("Conteudo vindo de arquivo.\n", encoding="utf-8")

    exit_code = main(
        [
            "inject",
            "roteiro",
            "demo-roteiro",
            "--descricao",
            "Um roteiro",
            "--conteudo-file",
            str(conteudo_path),
            "--path",
            str(tmp_path),
        ]
    )

    assert exit_code == 0
    dest = tmp_path / "tutoriais" / "demo-roteiro.md"
    assert dest.read_text(encoding="utf-8") == "Conteudo vindo de arquivo.\n"


def test_main_inject_falha_reporta_erros_e_sai_com_1(tmp_path: Path, capsys) -> None:
    exit_code = main(
        [
            "inject",
            "spec",
            "demo-spec",
            "--descricao",
            "Uma spec",
            "--conteudo",
            "pass",
            "--path",
            str(tmp_path),
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "falhou" in output
