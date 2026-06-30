# deploy.ps1 - sincroniza o monolito para ..\rpg-api-deploy com travas de seguranca.
# Faz o mirror, checa que nada proibido vazou, mostra o git status e PARA.
# Commit e push sao MANUAIS - este script NAO commita nem da push.

$ErrorActionPreference = 'Stop'

$origem  = $PSScriptRoot
$destino = Join-Path $PSScriptRoot '..\rpg-api-deploy'

if (-not (Test-Path $destino)) {
    Write-Error "Destino nao encontrado: $destino"
    exit 1
}

# 1) Mirror com a MESMA lista de exclusao de sempre.
robocopy $origem $destino /MIR /XD .git .claude __pycache__ .venv .hypothesis .pytest_cache /XF .env *.log *.pyc deploy.ps1 /NFL /NDL /NJH | Out-Null

# robocopy: exit 0-7 = ok (copiou / extras / etc); >= 8 = erro real.
if ($LASTEXITCODE -ge 8) {
    Write-Error "robocopy falhou (exit $LASTEXITCODE)."
    exit 1
}

# 2) Rede de seguranca: nada de segredo (.env) nem teimosos no destino.
$proibidos = @('.env', 'jogar_gravura.zip', 'smoke_opus.py')
$vazou = $proibidos | Where-Object { Test-Path (Join-Path $destino $_) }

if ($vazou) {
    Write-Error "ABORTADO: arquivo(s) proibido(s) no destino: $($vazou -join ', ')"
    exit 1
}

# 3) git status do destino para revisao.
Write-Host ""
Write-Host "=== git status --short ($destino) ==="
Push-Location $destino
git status --short
Pop-Location

# 4) PARA aqui de proposito. Revise o status acima e rode manualmente:
#      cd ..\rpg-api-deploy
#      git add -A
#      git commit -m "sua mensagem"
#      git push origin main
Write-Host ""
Write-Host "Sincronizacao OK e travas passaram. Commit/push sao MANUAIS - este script NAO commita."