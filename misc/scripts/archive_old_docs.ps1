# Archive Old Documentation Files
# Moves all old documentation files to archive/ while preserving 14 new consolidated docs

$ErrorActionPreference = "Stop"

# Files to KEEP (new consolidated documents)
$keepFiles = @(
    "ARCH_logging_system.md",
    "ARCH_node_system.md",
    "ARCH_command_system.md",
    "ARCH_memory_system.md",
    "TECH_token_management.md",
    "TECH_optimization_consolidation.md",
    "TECH_commander_window.md",
    "BLUEPRINT_bstool_integration.md",
    "BLUEPRINT_context_menu.md",
    "BLUEPRINT_integration_points.md",
    "BLUEPRINT_implementation_phases.md",
    "GUIDE_user_documentation.md",
    "ROADMAP_project_planning.md",
    "index.md",
    "index.md.old_backup"
)

# Directories to process
$directories = @(
    @{Source = "architecture"; Keep = @("ARCH_logging_system.md", "ARCH_node_system.md", "ARCH_command_system.md", "ARCH_memory_system.md")},
    @{Source = "technical"; Keep = @("TECH_token_management.md", "TECH_optimization_consolidation.md", "TECH_commander_window.md")},
    @{Source = "blueprints"; Keep = @("BLUEPRINT_bstool_integration.md", "BLUEPRINT_context_menu.md", "BLUEPRINT_integration_points.md", "BLUEPRINT_implementation_phases.md")},
    @{Source = "guides"; Keep = @("GUIDE_user_documentation.md")},
    @{Source = "roadmap"; Keep = @("ROADMAP_project_planning.md")}
)

$movedCount = 0
$keepCount = 0
$totalCount = 0

Write-Host "=== Documentation Archival Script ===" -ForegroundColor Cyan
Write-Host "Archiving old documentation files to docs/archive/" -ForegroundColor Cyan
Write-Host ""

foreach ($dir in $directories) {
    $sourcePath = "d:\_APP\LOGReport\docs\$($dir.Source)"
    $archivePath = "d:\_APP\LOGReport\docs\archive\$($dir.Source)"
    
    Write-Host "Processing: docs/$($dir.Source)/" -ForegroundColor Yellow
    
    if (Test-Path $sourcePath) {
        $files = Get-ChildItem -Path $sourcePath -Filter "*.md" -File
        
        foreach ($file in $files) {
            $totalCount++
            
            if ($dir.Keep -contains $file.Name) {
                Write-Host "  [KEEP] $($file.Name)" -ForegroundColor Green
                $keepCount++
            } else {
                $destination = Join-Path $archivePath $file.Name
                Move-Item -Path $file.FullName -Destination $destination -Force
                Write-Host "  [MOVE] $($file.Name) -> archive/$($dir.Source)/" -ForegroundColor Cyan
                $movedCount++
            }
        }
    }
    Write-Host ""
}

# Archive root-level docs (excluding index.md and index.md.old_backup)
Write-Host "Processing: docs/ (root level)" -ForegroundColor Yellow
$rootPath = "d:\_APP\LOGReport\docs"
$rootFiles = Get-ChildItem -Path $rootPath -Filter "*.md" -File | Where-Object { 
    $_.Name -notin @("index.md", "index.md.old_backup")
}

foreach ($file in $rootFiles) {
    $totalCount++
    $destination = Join-Path "d:\_APP\LOGReport\docs\archive" $file.Name
    Move-Item -Path $file.FullName -Destination $destination -Force
    Write-Host "  [MOVE] $($file.Name) -> archive/" -ForegroundColor Cyan
    $movedCount++
}

Write-Host ""
Write-Host "=== Archival Complete ===" -ForegroundColor Green
Write-Host "Total files processed: $totalCount" -ForegroundColor White
Write-Host "Files kept (new docs): $keepCount" -ForegroundColor Green
Write-Host "Files archived (old docs): $movedCount" -ForegroundColor Cyan
Write-Host ""
Write-Host "Kept documents:" -ForegroundColor Yellow
foreach ($file in $keepFiles | Where-Object { $_ -ne "index.md.old_backup" }) {
    Write-Host "  + $file" -ForegroundColor Green
}
