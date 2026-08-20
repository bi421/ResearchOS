# Collect ResearchOS evidence

Write-Host "Collecting repository evidence..."


tree /F > AI_TREE.txt


git status > AI_GIT_STATUS.txt


git log -5 --oneline > AI_GIT_HISTORY.txt


Get-ChildItem -Recurse -Include *.py,*.cpp,*.h |
Select-Object FullName |
Out-File AI_SOURCE_FILES.txt


pytest --collect-only -q |
Out-File AI_TEST_INDEX.txt


Write-Host "Evidence collection complete."

