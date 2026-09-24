#define MyAppName "Sistema de Turnos"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Sistema de Turnos"
#define MyAppExeName "Sistema de Turnos.exe"

[Setup]
AppId={{B5B4F82D-67C2-44B6-AE70-7A0BF86D0D7D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\Sistema de Turnos
DefaultGroupName={#MyAppName}
OutputDir=..\dist\installer
OutputBaseFilename=SistemaDeTurnos-Setup-{#MyAppVersion}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin

[Files]
Source: "..\dist\Sistema de Turnos.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"

[UninstallDelete]
Type: filesandordirs; Name: "{userappdata}\Sistema de Turnos"
