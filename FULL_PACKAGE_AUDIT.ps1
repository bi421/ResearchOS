Set-StrictMode -Version Latest
$ErrorActionPreference = "Continue"

$Root = (Get-Location).Path
$Out = Join-Path $Root "AUDIT_REPORT"

# ------------------------------------------------------------
# RESET REPORT DIRECTORY
# ------------------------------------------------------------

if (Test-Path -LiteralPath $Out) {
    Remove-Item -LiteralPath $Out -Recurse -Force -ErrorAction SilentlyContinue
}

New-Item -ItemType Directory -Path $Out -Force | Out-Null

$Report = Join-Path $Out "FULL_AUDIT.txt"

# ------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------

function Section {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Title
    )

    Add-Content -LiteralPath $Report ""
    Add-Content -LiteralPath $Report ("=" * 100)
    Add-Content -LiteralPath $Report $Title
    Add-Content -LiteralPath $Report ("=" * 100)
}

function Run-Cmd {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Label,

        [Parameter(Mandatory = $true)]
        [string]$Cmd
    )

    Add-Content -LiteralPath $Report ""
    Add-Content -LiteralPath $Report "--- $Label ---"

    try {
        $result = @(Invoke-Expression $Cmd 2>&1)

        if ($result.Count -gt 0) {
            $result |
                Out-String |
                Add-Content -LiteralPath $Report
        }
        else {
            Add-Content -LiteralPath $Report "[NO OUTPUT]"
        }
    }
    catch {
        Add-Content -LiteralPath $Report "ERROR: $($_.Exception.Message)"
    }
}

function Get-RelativePath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FullPath
    )

    if ($FullPath.StartsWith($Root, [System.StringComparison]::OrdinalIgnoreCase)) {
        return $FullPath.Substring($Root.Length).TrimStart('\')
    }

    return $FullPath
}

function Get-PythonFiles {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        return @()
    }

    return @(
        Get-ChildItem `
            -LiteralPath $Path `
            -Filter "*.py" `
            -File `
            -Recurse `
            -ErrorAction SilentlyContinue
    )
}

function Get-AllDirectories {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        return @()
    }

    return @(
        Get-ChildItem `
            -LiteralPath $Path `
            -Directory `
            -Recurse `
            -ErrorAction SilentlyContinue |
        Sort-Object FullName
    )
}

function Get-AllFiles {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        return @()
    }

    return @(
        Get-ChildItem `
            -LiteralPath $Path `
            -File `
            -Recurse `
            -ErrorAction SilentlyContinue
    )
}

# ------------------------------------------------------------
# INITIAL REPORT
# ------------------------------------------------------------

"ResearchOS FORENSIC PACKAGE AUDIT" |
    Set-Content -LiteralPath $Report

"Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" |
    Add-Content -LiteralPath $Report

"Root: $Root" |
    Add-Content -LiteralPath $Report

"Mode: READ-ONLY" |
    Add-Content -LiteralPath $Report

# ============================================================
# 1. ENVIRONMENT
# ============================================================

Section "1. ENVIRONMENT"

Run-Cmd "Python" "python --version"
Run-Cmd "Pytest" "python -m pytest --version"
Run-Cmd "Git" "git --version"
Run-Cmd "Git branch/status" "git status -sb"
Run-Cmd "HEAD" "git rev-parse HEAD"
Run-Cmd "Origin HEAD" "git rev-parse origin/main"
Run-Cmd "Recent commits" "git log -10 --oneline --decorate"

# ============================================================
# 2. PACKAGE INVENTORY
# ============================================================

Section "2. PACKAGE INVENTORY"

$PackageRoot = Join-Path $Root "researchos"

$dirs = @()
$pyFiles = @()
$Tests = Join-Path $Root "researchos\tests"
$testFiles = @()

if (-not (Test-Path -LiteralPath $PackageRoot)) {

    Add-Content -LiteralPath $Report `
        "ERROR: researchos package not found at $PackageRoot"

}
else {

    $dirs = @(Get-AllDirectories -Path $PackageRoot)
    $pyFiles = @(Get-PythonFiles -Path $PackageRoot)

    Add-Content -LiteralPath $Report "PACKAGE DIRECTORIES:"
    Add-Content -LiteralPath $Report ""

    if ($dirs.Count -eq 0) {
        Add-Content -LiteralPath $Report "[NONE]"
    }
    else {
        foreach ($d in $dirs) {
            $relative = Get-RelativePath -FullPath $d.FullName
            Add-Content -LiteralPath $Report $relative
        }
    }

    Add-Content -LiteralPath $Report ""
    Add-Content -LiteralPath $Report "PYTHON FILE COUNTS:"
    Add-Content -LiteralPath $Report ""

    if ($dirs.Count -eq 0) {

        Add-Content -LiteralPath $Report "[NO SUBDIRECTORIES]"

    }
    else {

        foreach ($d in $dirs) {

            $files = @(
                Get-ChildItem `
                    -LiteralPath $d.FullName `
                    -Filter "*.py" `
                    -File `
                    -Recurse `
                    -ErrorAction SilentlyContinue
            )

            $fileCount = $files.Count

            if ($fileCount -gt 0) {

                $relative = Get-RelativePath -FullPath $d.FullName

                Add-Content -LiteralPath $Report `
                    ("{0,-60} {1,6}" -f $relative, $fileCount)
            }
        }
    }
}

# ============================================================
# 3. TOP-LEVEL PYTHON FILES
# ============================================================

Section "3. TOP-LEVEL PYTHON FILES"

if (-not (Test-Path -LiteralPath $PackageRoot)) {

    Add-Content -LiteralPath $Report "[researchos package missing]"

}
else {

    $topLevelPython = @(
        Get-ChildItem `
            -LiteralPath $PackageRoot `
            -Filter "*.py" `
            -File `
            -ErrorAction SilentlyContinue
    )

    if ($topLevelPython.Count -eq 0) {

        Add-Content -LiteralPath $Report "[NONE]"

    }
    else {

        $topLevelPython |
            Select-Object FullName, Length, LastWriteTime |
            Format-Table -AutoSize |
            Out-String |
            Add-Content -LiteralPath $Report
    }
}

# ============================================================
# 4. FILE SIZE / EMPTY / SUSPICIOUS FILES
# ============================================================

Section "4. EMPTY / SUSPICIOUS PYTHON FILES"

if ($pyFiles.Count -eq 0) {

    Add-Content -LiteralPath $Report "[NO PYTHON FILES]"

}
else {

    foreach ($f in $pyFiles) {

        $contentLines = @(
            Get-Content `
                -LiteralPath $f.FullName `
                -ErrorAction SilentlyContinue
        )

        $lines = $contentLines.Count
        $bytes = $f.Length

        if (($lines -le 5) -or ($bytes -lt 100)) {

            $relative = Get-RelativePath -FullPath $f.FullName

            Add-Content -LiteralPath $Report `
                "SUSPICIOUS: $relative | lines=$lines | bytes=$bytes"
        }
    }
}

# ============================================================
# 5. TODO / FIXME / PASS / NOTIMPLEMENTED
# ============================================================

Section "5. TODO / FIXME / PASS / NOTIMPLEMENTED / STUBS"

$patterns = @(
    "TODO",
    "FIXME",
    "XXX",
    "NotImplemented",
    "NotImplementedError",
    "raise NotImplemented",
    "pass\s*$",
    "stub",
    "placeholder",
    "coming soon"
)

foreach ($pattern in $patterns) {

    Add-Content -LiteralPath $Report ""
    Add-Content -LiteralPath $Report "### PATTERN: $pattern"

    if ($pyFiles.Count -eq 0) {
        Add-Content -LiteralPath $Report "[NO PYTHON FILES]"
        continue
    }

    $matches = @(
        $pyFiles |
            Select-String `
                -Pattern $pattern `
                -CaseSensitive:$false `
                -ErrorAction SilentlyContinue
    )

    if ($matches.Count -eq 0) {

        Add-Content -LiteralPath $Report "[NO MATCHES]"

    }
    else {

        foreach ($match in $matches) {

            $relative = Get-RelativePath -FullPath $match.Path

            Add-Content -LiteralPath $Report `
                "${relative}:$($match.LineNumber): $($match.Line.Trim())"
        }
    }
}

# ============================================================
# 6. IMPORT STRUCTURE
# ============================================================

Section "6. IMPORT STRUCTURE"

if ($pyFiles.Count -eq 0) {

    Add-Content -LiteralPath $Report "[NO PYTHON FILES]"

}
else {

    $imports = @(
        $pyFiles |
            Select-String `
                -Pattern "^(from|import)\s" `
                -ErrorAction SilentlyContinue
    )

    if ($imports.Count -eq 0) {

        Add-Content -LiteralPath $Report "[NO IMPORTS FOUND]"

    }
    else {

        foreach ($match in $imports) {

            $relative = Get-RelativePath -FullPath $match.Path

            Add-Content -LiteralPath $Report `
                "${relative}:$($match.LineNumber): $($match.Line.Trim())"
        }
    }
}

# ============================================================
# 7. DUPLICATE FILE NAMES
# ============================================================

Section "7. DUPLICATE FILE NAMES"

if ($pyFiles.Count -eq 0) {

    Add-Content -LiteralPath $Report "[NO PYTHON FILES]"

}
else {

    $duplicateNames = @(
        $pyFiles |
            Group-Object Name |
            Where-Object { $_.Count -gt 1 }
    )

    if ($duplicateNames.Count -eq 0) {

        Add-Content -LiteralPath $Report "[NO DUPLICATE PYTHON FILE NAMES]"

    }
    else {

        foreach ($g in $duplicateNames) {

            Add-Content -LiteralPath $Report ""
            Add-Content -LiteralPath $Report `
                "DUPLICATE NAME: $($g.Name)"

            foreach ($item in @($g.Group)) {

                Add-Content -LiteralPath $Report `
                    ("  " + (Get-RelativePath -FullPath $item.FullName))
            }
        }
    }
}

# ============================================================
# 8. DUPLICATE CONTENT HASHES
# ============================================================

Section "8. DUPLICATE CONTENT HASHES"

if ($pyFiles.Count -eq 0) {

    Add-Content -LiteralPath $Report "[NO PYTHON FILES]"

}
else {

    $hashRecords = @()

    foreach ($file in $pyFiles) {

        try {

            $hash = Get-FileHash `
                -LiteralPath $file.FullName `
                -Algorithm SHA256 `
                -ErrorAction Stop

            $hashRecords += $hash

        }
        catch {

            Add-Content -LiteralPath $Report `
                "HASH ERROR: $($file.FullName) | $($_.Exception.Message)"
        }
    }

    $hashGroups = @(
        $hashRecords |
            Group-Object Hash |
            Where-Object { $_.Count -gt 1 }
    )

    if ($hashGroups.Count -eq 0) {

        Add-Content -LiteralPath $Report `
            "[NO DUPLICATE CONTENT HASHES]"

    }
    else {

        foreach ($g in $hashGroups) {

            Add-Content -LiteralPath $Report ""
            Add-Content -LiteralPath $Report `
                "DUPLICATE CONTENT HASH: $($g.Name)"

            foreach ($item in @($g.Group)) {

                Add-Content -LiteralPath $Report `
                    ("  " + (Get-RelativePath -FullPath $item.Path))
            }
        }
    }
}

# ============================================================
# 9. PACKAGE INIT FILES
# ============================================================

Section "9. PACKAGE __init__.py COVERAGE"

if (-not (Test-Path -LiteralPath $PackageRoot)) {

    Add-Content -LiteralPath $Report "[researchos package missing]"

}
else {

    if ($dirs.Count -eq 0) {

        Add-Content -LiteralPath $Report "[NO SUBDIRECTORIES]"

    }
    else {

        $missingInit = 0

        foreach ($d in $dirs) {

            $init = Join-Path $d.FullName "__init__.py"

            if (-not (Test-Path -LiteralPath $init)) {

                $missingInit++

                Add-Content -LiteralPath $Report `
                    "MISSING __init__.py: $(Get-RelativePath -FullPath $d.FullName)"
            }
        }

        if ($missingInit -eq 0) {

            Add-Content -LiteralPath $Report `
                "[ALL PACKAGE DIRECTORIES HAVE __init__.py]"

        }
    }
}

# ============================================================
# 10. TEST INVENTORY
# ============================================================

Section "10. TEST INVENTORY"

if (Test-Path -LiteralPath $Tests) {

    $testFiles = @(
        Get-ChildItem `
            -LiteralPath $Tests `
            -Filter "*.py" `
            -File `
            -Recurse `
            -ErrorAction SilentlyContinue
    )

    Add-Content -LiteralPath $Report `
        "Test files: $($testFiles.Count)"

    if ($testFiles.Count -gt 0) {

        $testFiles |
            Select-Object FullName, Length |
            Format-Table -AutoSize |
            Out-String |
            Add-Content -LiteralPath $Report
    }

}
else {

    Add-Content -LiteralPath $Report `
        "ERROR: Tests directory not found: $Tests"

    $testFiles = @()
}

# ============================================================
# 11. ALL TESTS
# ============================================================

Section "11. FULL PYTEST"

Run-Cmd "Full pytest" "python -m pytest -q"

# ============================================================
# 12. TEST COLLECTION
# ============================================================

Section "12. PYTEST COLLECTION"

Run-Cmd "Pytest collect-only" "python -m pytest --collect-only -q"

# ============================================================
# 13. COMPILEALL
# ============================================================

Section "13. PYTHON COMPILEALL"

Run-Cmd "Compile all" "python -m compileall -q researchos"

# ============================================================
# 14. RUFF
# ============================================================

Section "14. RUFF"

Run-Cmd "Ruff check" "python -m ruff check researchos"

Run-Cmd "Ruff format check" "python -m ruff format --check researchos"

# ============================================================
# 15. MAJOR PACKAGE TEST MATRIX
# ============================================================

Section "15. MAJOR PACKAGE TEST MATRIX"

$MajorPackages = @(
    "core",
    "data_engine",
    "market_memory",
    "quant_engine",
    "engines",
    "decision",
    "macro",
    "research",
    "experiments",
    "evidence",
    "intelligence",
    "validation",
    "orchestration",
    "cli",
    "capabilities"
)

foreach ($pkg in $MajorPackages) {

    $path = Join-Path $PackageRoot $pkg

    Add-Content -LiteralPath $Report ""
    Add-Content -LiteralPath $Report `
        ("### PACKAGE: {0}" -f $pkg)

    if (-not (Test-Path -LiteralPath $path)) {

        Add-Content -LiteralPath $Report "STATUS: MISSING"
        continue
    }

    $files = @(
        Get-PythonFiles -Path $path
    )

    $count = $files.Count

    Add-Content -LiteralPath $Report `
        "Python files: $count"

    if ($testFiles.Count -gt 0) {

        $testMatches = @(
            $testFiles |
                Select-String `
                    -Pattern $pkg `
                    -SimpleMatch `
                    -CaseSensitive:$false `
                    -ErrorAction SilentlyContinue
        )

    }
    else {

        $testMatches = @()
    }

    Add-Content -LiteralPath $Report `
        "Test references: $($testMatches.Count)"

    if ($files.Count -gt 0) {

        $todo = @(
            $files |
                Select-String `
                    -Pattern "TODO|FIXME|NotImplemented|placeholder|pass\s*$" `
                    -CaseSensitive:$false `
                    -ErrorAction SilentlyContinue
        )

    }
    else {

        $todo = @()
    }

    Add-Content -LiteralPath $Report `
        "Suspicious/stub matches: $($todo.Count)"

    if ($count -eq 0) {

        Add-Content -LiteralPath $Report `
            "CLASSIFICATION: EMPTY / SCAFFOLD"

    }
    elseif ($testMatches.Count -eq 0) {

        Add-Content -LiteralPath $Report `
            "CLASSIFICATION: IMPLEMENTED? BUT NO DIRECT TEST REFERENCE"

    }
    elseif ($todo.Count -gt 0) {

        Add-Content -LiteralPath $Report `
            "CLASSIFICATION: IMPLEMENTED BUT NEEDS REVIEW"

    }
    else {

        Add-Content -LiteralPath $Report `
            "CLASSIFICATION: IMPLEMENTED + TEST REFERENCES"
    }
}

# ============================================================
# 16. CLASS / FUNCTION INVENTORY
# ============================================================

Section "16. CLASS / FUNCTION INVENTORY"

if ($pyFiles.Count -eq 0) {

    Add-Content -LiteralPath $Report "[NO PYTHON FILES]"

}
else {

    $symbols = @(
        $pyFiles |
            Select-String `
                -Pattern "^\s*(class|def|async def)\s+" `
                -ErrorAction SilentlyContinue
    )

    if ($symbols.Count -eq 0) {

        Add-Content -LiteralPath $Report "[NO CLASS/FUNCTION DEFINITIONS FOUND]"

    }
    else {

        foreach ($match in $symbols) {

            $relative = Get-RelativePath -FullPath $match.Path

            Add-Content -LiteralPath $Report `
                "${relative}:$($match.LineNumber): $($match.Line.Trim())"
        }
    }
}

# ============================================================
# 17. EVIDENCE PIPELINE
# ============================================================

Section "17. EVIDENCE PIPELINE"

$EvidenceKeywords = @(
    "EvidenceEnvelope",
    "EvidenceRepository",
    "Run",
    "Result",
    "Validation",
    "lineage",
    "experiment_id",
    "run_hash",
    "result_hash",
    "validation_hash"
)

foreach ($keyword in $EvidenceKeywords) {

    Add-Content -LiteralPath $Report ""
    Add-Content -LiteralPath $Report "### $keyword"

    if ($pyFiles.Count -eq 0) {

        Add-Content -LiteralPath $Report "[NO PYTHON FILES]"
        continue
    }

    $matches = @(
        $pyFiles |
            Select-String `
                -Pattern $keyword `
                -CaseSensitive:$false `
                -ErrorAction SilentlyContinue
    )

    if ($matches.Count -eq 0) {

        Add-Content -LiteralPath $Report "[NO MATCHES]"

    }
    else {

        foreach ($match in $matches) {

            $relative = Get-RelativePath -FullPath $match.Path

            Add-Content -LiteralPath $Report `
                "${relative}:$($match.LineNumber): $($match.Line.Trim())"
        }
    }
}

# ============================================================
# 18. REGISTRY INVENTORY
# ============================================================

Section "18. REGISTRY INVENTORY"

if ($pyFiles.Count -eq 0) {

    Add-Content -LiteralPath $Report "[NO PYTHON FILES]"

}
else {

    $registryMatches = @(
        $pyFiles |
            Select-String `
                -Pattern "class .*Registry|Registry" `
                -CaseSensitive:$false `
                -ErrorAction SilentlyContinue
    )

    if ($registryMatches.Count -eq 0) {

        Add-Content -LiteralPath $Report "[NO REGISTRY REFERENCES]"

    }
    else {

        foreach ($match in $registryMatches) {

            $relative = Get-RelativePath -FullPath $match.Path

            Add-Content -LiteralPath $Report `
                "${relative}:$($match.LineNumber): $($match.Line.Trim())"
        }
    }
}

# ============================================================
# 19. RISK / PORTFOLIO
# ============================================================

Section "19. RISK / PORTFOLIO INVENTORY"

$RiskTerms = @(
    "VaR",
    "CVaR",
    "Kelly",
    "drawdown",
    "Sharpe",
    "Sortino",
    "position sizing",
    "portfolio",
    "risk"
)

foreach ($term in $RiskTerms) {

    Add-Content -LiteralPath $Report ""
    Add-Content -LiteralPath $Report "### $term"

    if ($pyFiles.Count -eq 0) {

        Add-Content -LiteralPath $Report "[NO PYTHON FILES]"
        continue
    }

    $matches = @(
        $pyFiles |
            Select-String `
                -Pattern $term `
                -CaseSensitive:$false `
                -ErrorAction SilentlyContinue
    )

    if ($matches.Count -eq 0) {

        Add-Content -LiteralPath $Report "[NO MATCHES]"

    }
    else {

        foreach ($match in $matches) {

            $relative = Get-RelativePath -FullPath $match.Path

            Add-Content -LiteralPath $Report `
                "${relative}:$($match.LineNumber): $($match.Line.Trim())"
        }
    }
}

# ============================================================
# 20. EXPERIMENT / RESEARCH INVENTORY
# ============================================================

Section "20. EXPERIMENT / RESEARCH INVENTORY"

$ResearchTerms = @(
    "Experiment",
    "ExperimentRun",
    "Research",
    "backtest",
    "simulation",
    "comparison",
    "benchmark",
    "hypothesis"
)

foreach ($term in $ResearchTerms) {

    Add-Content -LiteralPath $Report ""
    Add-Content -LiteralPath $Report "### $term"

    if ($pyFiles.Count -eq 0) {

        Add-Content -LiteralPath $Report "[NO PYTHON FILES]"
        continue
    }

    $matches = @(
        $pyFiles |
            Select-String `
                -Pattern $term `
                -CaseSensitive:$false `
                -ErrorAction SilentlyContinue
    )

    if ($matches.Count -eq 0) {

        Add-Content -LiteralPath $Report "[NO MATCHES]"

    }
    else {

        foreach ($match in $matches) {

            $relative = Get-RelativePath -FullPath $match.Path

            Add-Content -LiteralPath $Report `
                "${relative}:$($match.LineNumber): $($match.Line.Trim())"
        }
    }
}

# ============================================================
# 21. DOCUMENTATION CLAIMS
# ============================================================

Section "21. DOCUMENTATION FILES"

$Docs = Join-Path $Root "docs"

if (Test-Path -LiteralPath $Docs) {

    $docFiles = @(
        Get-ChildItem `
            -LiteralPath $Docs `
            -Filter "*.md" `
            -File `
            -Recurse `
            -ErrorAction SilentlyContinue
    )

    Add-Content -LiteralPath $Report `
        "Documentation files: $($docFiles.Count)"

    if ($docFiles.Count -gt 0) {

        $docFiles |
            Select-Object FullName, Length |
            Format-Table -AutoSize |
            Out-String |
            Add-Content -LiteralPath $Report

        Add-Content -LiteralPath $Report ""
        Add-Content -LiteralPath $Report `
            "ROADMAP / STATUS / IMPLEMENTATION CLAIMS:"

        $docMatches = @(
            $docFiles |
                Select-String `
                    -Pattern "implemented|complete|planned|future|roadmap|frozen|current|missing" `
                    -CaseSensitive:$false `
                    -ErrorAction SilentlyContinue
        )

        if ($docMatches.Count -eq 0) {

            Add-Content -LiteralPath $Report "[NO STATUS CLAIMS FOUND]"

        }
        else {

            foreach ($match in $docMatches) {

                $relative = Get-RelativePath -FullPath $match.Path

                Add-Content -LiteralPath $Report `
                    "${relative}:$($match.LineNumber): $($match.Line.Trim())"
            }
        }
    }

}
else {

    Add-Content -LiteralPath $Report `
        "ERROR: docs directory not found: $Docs"
}

# ============================================================
# 22. GIT TRACKING
# ============================================================

Section "22. GIT TRACKING"

Run-Cmd "Git status" "git status --short"
Run-Cmd "Untracked files" "git ls-files --others --exclude-standard"
Run-Cmd "Modified tracked files" "git diff --name-only"
Run-Cmd "Staged files" "git diff --cached --name-only"
Run-Cmd "Tracked Python files" "git ls-files '*.py'"
Run-Cmd "Tracked test files" "git ls-files '*test*.py'"

# ============================================================
# 23. GENERATED / BUILD ARTIFACTS
# ============================================================

Section "23. GENERATED / BUILD ARTIFACTS"

$artifactPatterns = @(
    "*.pyc",
    "*.pyd",
    "*.dll",
    "*.exe",
    "*.obj",
    "*.o",
    "*.lib",
    "*.pdb",
    "*.coverage",
    "coverage.xml",
    ".coverage",
    "*.log"
)

foreach ($pattern in $artifactPatterns) {

    $found = @(
        Get-ChildItem `
            -LiteralPath $Root `
            -Filter $pattern `
            -File `
            -Recurse `
            -ErrorAction SilentlyContinue
    )

    if ($found.Count -gt 0) {

        Add-Content -LiteralPath $Report ""
        Add-Content -LiteralPath $Report `
            "### $pattern : $($found.Count)"

        foreach ($f in $found) {

            Add-Content -LiteralPath $Report `
                (Get-RelativePath -FullPath $f.FullName)
        }
    }
    else {

        Add-Content -LiteralPath $Report `
            "### $pattern : 0"
    }
}

# ============================================================
# 24. LARGE FILES
# ============================================================

Section "24. LARGE FILES"

$largeFiles = @(
    Get-ChildItem `
        -LiteralPath $Root `
        -File `
        -Recurse `
        -ErrorAction SilentlyContinue |
    Where-Object { $_.Length -gt 5MB } |
    Sort-Object Length -Descending
)

if ($largeFiles.Count -eq 0) {

    Add-Content -LiteralPath $Report "[NO FILES > 5 MB]"

}
else {

    $largeFileOutput = @(
        $largeFiles |
            Select-Object @{
                Name = "MB"
                Expression = {
                    [math]::Round($_.Length / 1MB, 2)
                }
            }, FullName
    )

    $largeFileOutput |
        Format-Table -AutoSize |
        Out-String |
        Add-Content -LiteralPath $Report
}

# ============================================================
# 25. FINAL MACHINE SUMMARY
# ============================================================

Section "25. FINAL MACHINE SUMMARY"

$allPy = @(
    Get-PythonFiles -Path $PackageRoot
)

$allTests = @(
    Get-PythonFiles -Path $Tests
)

$finalHead = ""
$finalOrigin = ""

try {
    $finalHead = (git rev-parse HEAD 2>$null | Out-String).Trim()
}
catch {
    $finalHead = "UNAVAILABLE"
}

try {
    $finalOrigin = (git rev-parse origin/main 2>$null | Out-String).Trim()
}
catch {
    $finalOrigin = "UNAVAILABLE"
}

Add-Content -LiteralPath $Report `
    "Total production Python files : $($allPy.Count)"

Add-Content -LiteralPath $Report `
    "Total test Python files       : $($allTests.Count)"

Add-Content -LiteralPath $Report `
    "Package directories           : $($dirs.Count)"

Add-Content -LiteralPath $Report `
    "Git HEAD                      : $finalHead"

Add-Content -LiteralPath $Report `
    "Origin/main                   : $finalOrigin"

Add-Content -LiteralPath $Report ""
Add-Content -LiteralPath $Report "Working tree:"

$finalStatus = @(
    git status --short 2>&1
)

if ($finalStatus.Count -eq 0) {

    Add-Content -LiteralPath $Report "[CLEAN]"

}
else {

    $finalStatus |
        Out-String |
        Add-Content -LiteralPath $Report
}

# ============================================================
# FINAL INTEGRITY INFORMATION
# ============================================================

Add-Content -LiteralPath $Report ""
Add-Content -LiteralPath $Report ("=" * 100)
Add-Content -LiteralPath $Report "AUDIT EXECUTION INTEGRITY"
Add-Content -LiteralPath $Report ("=" * 100)

Add-Content -LiteralPath $Report `
    "Script mode: READ-ONLY"

Add-Content -LiteralPath $Report `
    "Source modification commands used: NONE"

Add-Content -LiteralPath $Report `
    "Report directory recreated: YES"

Add-Content -LiteralPath $Report `
    "Audit completed: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"

Add-Content -LiteralPath $Report ""
Add-Content -LiteralPath $Report "AUDIT COMPLETE."
Add-Content -LiteralPath $Report `
    "NO SOURCE FILES WERE INTENTIONALLY MODIFIED BY THIS SCRIPT."

# ============================================================
# CONSOLE OUTPUT
# ============================================================

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " RESEARCHOS FORENSIC PACKAGE AUDIT COMPLETE" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Report:" -ForegroundColor Yellow
Write-Host $Report -ForegroundColor White
Write-Host ""
Write-Host "Production Python files: $($allPy.Count)" -ForegroundColor White
Write-Host "Test Python files      : $($allTests.Count)" -ForegroundColor White
Write-Host "Package directories    : $($dirs.Count)" -ForegroundColor White
Write-Host ""
Write-Host "Read-only audit: source code was not modified." -ForegroundColor Green
Write-Host ""
