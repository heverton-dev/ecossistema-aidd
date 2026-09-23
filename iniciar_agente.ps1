
$Host.UI.RawUI.WindowTitle = "AIDD_TTY_Efemero_1790196192"
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  AIDD 4F - AGENTE INTERATIVO AO VIVO" -ForegroundColor Green
Write-Host "  Worktree: $PWD" -ForegroundColor Yellow
Write-Host "  Comando: claude --dangerously-skip-permissions --chrome --model opus" -ForegroundColor DarkGray
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

if (Test-Path "PROMPT_FASE.txt") {
    $prompt = Get-Content "PROMPT_FASE.txt" -Raw
    & claude --dangerously-skip-permissions --chrome --model opus $prompt
} else {
    & claude --dangerously-skip-permissions --chrome --model opus
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Execução do Agente finalizada. Pressione Enter para fechar." -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Read-Host
