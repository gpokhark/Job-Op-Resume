# convert_resume.ps1
# PostToolUse hook: converts resume files to PDF.
#   *_Resume_*.html -> measure_resume.py (Playwright) -> .pdf
#   *_Resume_*.md   -> build_resume.py (python-docx)  -> .docx -> docx2pdf -> .pdf
# Receives Claude tool event JSON on stdin.

param()

$stdinContent = [Console]::In.ReadToEnd()
if (-not $stdinContent) { exit 0 }

try {
    $event = $stdinContent | ConvertFrom-Json -ErrorAction Stop
} catch {
    exit 0
}

$filePath = $event.tool_input.file_path
if (-not $filePath) { exit 0 }
if (-not (Test-Path $filePath)) { exit 0 }

$repoRoot = "D:\github\Job-Op-Resume"

# ── HTML resume → PDF via Playwright ─────────────────────────────────────────
if ($filePath -match '_Resume_.*\.html$') {
    $pdfPath     = $filePath -replace '\.html$', '.pdf'
    $measureScript = "$repoRoot\scripts\measure_resume.py"

    $resultJson = & uv --directory $repoRoot run python $measureScript $filePath --save-pdf $pdfPath 2>&1
    try {
        $result = $resultJson | ConvertFrom-Json -ErrorAction Stop
        $fill   = $result.fill_pct
        $pages  = $result.pages
        $status = $result.status
    } catch {
        $fill = "?"; $pages = "?"; $status = "unknown"
    }

    if (Test-Path $pdfPath) {
        Write-Host "Resume converted: $([System.IO.Path]::GetFileNameWithoutExtension($filePath)) -> pdf | $pages page(s), $fill% full [$status]"
    } else {
        Write-Host "Resume HTML->PDF failed for: $filePath" -ForegroundColor Red
    }

    # ── Log to resume_log.csv ────────────────────────────────────────────────
    $folder      = Split-Path $filePath -Parent
    $fileName    = Split-Path $filePath -Leaf
    $date        = (Get-Date -Format "yyyy-MM-dd")

    # Extract company name from folder name
    $company = Split-Path $folder -Leaf

    # Extract role and job URL from JD file in the same folder
    $jdFile = Get-ChildItem $folder -Filter "JD_*.txt" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    $role = "Not specified"
    $jobUrl = "Not specified"
    if ($jdFile) {
        $jdLines = Get-Content $jdFile.FullName -TotalCount 15
        $role = $jdLines[0].Trim()
        $urlLine = $jdLines | Where-Object { $_ -match "^Job URL:" } | Select-Object -First 1
        if ($urlLine) { $jobUrl = ($urlLine -replace "^Job URL:\s*", "").Trim() }
    }

    # Read iteration count from sidecar file if present
    $iterFile = Join-Path $folder "_iterations.json"
    $iterations = "?"
    if (Test-Path $iterFile) {
        try {
            $iterData = Get-Content $iterFile -Raw | ConvertFrom-Json
            $iterations = $iterData.iterations
        } catch {}
        Remove-Item $iterFile -Force
    }

    $logScript = "$repoRoot\scripts\log_resume.py"
    & uv --directory $repoRoot run python $logScript `
        --file $fileName `
        --company $company `
        --role $role `
        --url $jobUrl `
        --fill $fill `
        --pages $pages `
        --iterations $iterations `
        --date $date 2>&1 | Out-Null

    exit 0
}

# ── Markdown resume → .docx + .pdf via python-docx / Word ───────────────────
if ($filePath -match '_Resume_.*\.md$') {
    $base        = $filePath -replace '\.md$', ''
    $docxPath    = "$base.docx"
    $pdfPath     = "$base.pdf"
    $buildScript = "$repoRoot\scripts\build_resume.py"

    & uv --directory $repoRoot run python $buildScript $filePath $docxPath 2>&1 | Out-Null
    & uv --directory $repoRoot run python -c "from docx2pdf import convert; convert(r'$docxPath', r'$pdfPath')" 2>&1 | Out-Null

    $results = @()
    if (Test-Path $docxPath) { $results += "docx" }
    if (Test-Path $pdfPath)  { $results += "pdf"  }

    if ($results.Count -gt 0) {
        Write-Host "Resume converted: $([System.IO.Path]::GetFileNameWithoutExtension($filePath)) -> $($results -join ', ')"
    } else {
        Write-Host "Resume conversion failed for: $filePath" -ForegroundColor Red
    }
    exit 0
}
