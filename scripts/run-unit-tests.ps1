<#
.SYNOPSIS
  Phase 5: run the team's white-box unit suite with branch coverage.

.DESCRIPTION
  1. Regenerates evidence/raw/get-status-truth-table.csv (the 128-row MCC table
     that parametrizes tests/team/unit/test_get_status_mcc.py - single source of truth).
  2. Runs pytest on tests/team/ with branch coverage over the measured files
     (hc/api/models.py + hc/api/decorators.py, see .coveragerc).

  Outputs:
    evidence/coverage.xml     (raw, also read by SonarQube)
    evidence/coverage-html/   (raw browsable HTML)

  Usage (from anywhere):  .\scripts\run-unit-tests.ps1
#>
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$py = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
    Write-Error "venv not found at $py - run scripts/setup or create the venv first"
    exit 1
}

# 1. Truth table (evidence) must exist before pytest collects the parametrized tests
& $py tools\unit\get_status_truth_table.py
if ($LASTEXITCODE -ne 0) { Write-Error "truth-table generation FAILED"; exit $LASTEXITCODE }

# 2. Test run with branch coverage
& $py -m pytest tests/team `
    --cov-config=.coveragerc `
    --cov=hc `
    --cov-branch `
    --cov-report=term-missing `
    --cov-report=html:evidence/coverage-html `
    --cov-report=xml:evidence/coverage.xml `
    -v
exit $LASTEXITCODE
