[Setup]
; Basic settings
AppName=YourAppName
AppVersion=1.0
DefaultDirName={pf}\YourAppName
DefaultGroupName=YourAppName
OutputDir=output
OutputBaseFilename=YourAppNameInstaller
Compression=lzma
SolidCompression=yes

; Installer attributes
[Files]
; Main executable
Source: "dist\YOKIProductUploader.exe"; DestDir: "{app}"; Flags: ignoreversion
; Include GeckoDriver
Source: "geckodriver.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Start menu icon
Name: "{group}\YourAppName"; Filename: "{app}\YourAppName.exe"

[Run]
; Run the application after installation
Filename: "{app}\YourAppName.exe"; Description: "{cm:LaunchProgram,YourAppName}"; Flags: nowait postinstall skipifsilent
