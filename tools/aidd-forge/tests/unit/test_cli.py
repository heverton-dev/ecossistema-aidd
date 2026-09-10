from pathlib import Path

from click.testing import CliRunner

from aidd_forge.cli import cli, main


def test_init_default_path_is_current_dir(tmp_path: Path) -> None:
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(cli, ["init"])

    assert result.exit_code == 0
    assert "projeto alvo:" in result.output


def test_init_force_flag(tmp_path: Path) -> None:
    exit_code = main(["init", str(tmp_path), "--force"])

    assert exit_code == 0


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


def test_build_parser_exposes_inject_subcommand(tmp_path: Path, capsys) -> None:
    exit_code = main(
        [
            "inject",
            "spec",
            "demo-spec",
            "--descricao",
            "Uma spec",
            "--conteudo",
            "Conteudo real.",
            "--path",
            str(tmp_path),
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "componente injetado: spec/demo-spec" in output


def test_inject_requires_conteudo_or_conteudo_file() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["inject", "spec", "demo-spec", "--descricao", "Uma spec"])

    assert result.exit_code == 2


def test_inject_rejects_unknown_tipo() -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli, ["inject", "agent", "demo", "--descricao", "x", "--conteudo", "y"]
    )

    assert result.exit_code == 2


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
