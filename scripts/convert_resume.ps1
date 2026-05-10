# convert_resume.ps1
# PostToolUse hook: converts *_Resume_*.md to .docx (python-docx) and .pdf (docx2pdf via Word).
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

# Only process resume markdown files (pattern: *_Resume_*.md)
if ($filePath -notmatch '_Resume_.*\.md$') { exit 0 }
if (-not (Test-Path $filePath)) { exit 0 }

$repoRoot  = "D:\github\Job-Op-Resume"
$base      = $filePath -replace '\.md$', ''
$docxPath  = "$base.docx"
$pdfPath   = "$base.pdf"
$buildScript = "$repoRoot\scripts\build_resume.py"

# --- .docx via python-docx (exact formatting: 0.5in margins, 16pt name, etc.) ---
& uv --directory $repoRoot run python $buildScript $filePath $docxPath 2>&1 | Out-Null

# --- .pdf via docx2pdf (converts .docx through Word — identical pagination and formatting) ---
& uv --directory $repoRoot run python -c "from docx2pdf import convert; convert(r'$docxPath', r'$pdfPath')" 2>&1 | Out-Null

$results = @()
if (Test-Path $docxPath) { $results += "docx" }
if (Test-Path $pdfPath)  { $results += "pdf"  }

if ($results.Count -gt 0) {
    Write-Host "Resume converted: $([System.IO.Path]::GetFileNameWithoutExtension($filePath)) -> $($results -join ', ')"
} else {
    Write-Host "Resume conversion failed for: $filePath" -ForegroundColor Red
}
