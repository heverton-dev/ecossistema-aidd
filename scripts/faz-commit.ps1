param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ScriptArgs
)

$scriptPath = Join-Path $PSScriptRoot "faz_commit.py"
& python $scriptPath @ScriptArgs
