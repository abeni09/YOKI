[Setup]
; Basic settings
AppName=YOKI
AppVersion=1.1
DefaultDirName={autopf}\YOKI
DefaultGroupName=YOKI
OutputDir=output
OutputBaseFilename=YOKI_Installer
Compression=lzma
SolidCompression=yes
SetupIconFile=logo.ico
UninstallDisplayIcon={app}\logo.ico
PrivilegesRequired=admin

[Dirs]
Name: "{app}"; Permissions: users-modify

[Files]
; Main executable
Source: "dist\YOKI.exe"; DestDir: "{app}"; Flags: ignoreversion
; Include GeckoDriver
Source: "geckodriver.exe"; DestDir: "{app}"; Flags: ignoreversion
; Database file with modify permissions
Source: "uploaded_products.db"; DestDir: "{app}"; Flags: ignoreversion; Permissions: users-modify
; Icon file
Source: "logo.ico"; DestDir: "{app}"; Flags: ignoreversion 

[Icons]
; Start menu and desktop icons
Name: "{autoprograms}\YOKI"; Filename: "{app}\YOKI.exe"; IconFilename: "{app}\logo.ico"
Name: "{autodesktop}\YOKI"; Filename: "{app}\YOKI.exe"; IconFilename: "{app}\logo.ico"

[Run]
; Set full permissions on the database file
Filename: "powershell.exe"; \
    Parameters: "-NoProfile -ExecutionPolicy Bypass -Command ""& {{$acl = Get-Acl '{app}\uploaded_products.db'; $rule = New-Object System.Security.AccessControl.FileSystemAccessRule('Users','FullControl','Allow'); $acl.SetAccessRule($rule); $acl | Set-Acl '{app}\uploaded_products.db'}}"""; \
    Flags: runhidden; StatusMsg: "Setting database permissions..."

; Run the application after installation
Filename: "{app}\YOKI.exe"; Description: "{cm:LaunchProgram,YOKI}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: files; Name: "{app}\*.*"
Type: dirifempty; Name: "{app}"
