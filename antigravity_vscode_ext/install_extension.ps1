cd " C:\WEB CASE STUDY\antigravity_vscode_ext\; npm install; npx @vscode/vsce package; $vsix = Get-ChildItem *.vsix | Select-Object -First 1; code --install-extension $vsix.FullName --force
