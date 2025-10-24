; Inno Setup Script for FileSync Windows Installer
; Requires Inno Setup 6.0 or later: https://jrsoftware.org/isinfo.php

#define MyAppName "FileSync"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "FileSync Team"
#define MyAppURL "https://github.com/IamSteveV/file-sync"
#define MyAppExeName "FileSync.exe"
#define MyAppCLIName "filesync.exe"

[Setup]
; NOTE: The value of AppId uniquely identifies this application. Do not use the same AppId value in installers for other applications.
AppId={{8C9F4A6D-2E3B-4F5C-9D1A-7B8E6C4F2A9D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=LICENSE
InfoBeforeFile=README.md
OutputDir=installer
OutputBaseFilename=FileSync-{#MyAppVersion}-Windows-Setup
SetupIconFile=assets\filesync.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; GUI Application
Source: "dist\FileSync-GUI\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\FileSync-GUI\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; CLI Application
Source: "dist\filesync-cli\{#MyAppCLIName}"; DestDir: "{app}\cli"; Flags: ignoreversion
Source: "dist\filesync-cli\*"; DestDir: "{app}\cli"; Flags: ignoreversion recursesubdirs createallsubdirs

; Documentation
Source: "README.md"; DestDir: "{app}\docs"; Flags: ignoreversion
Source: "ARCHITECTURE.md"; DestDir: "{app}\docs"; Flags: ignoreversion
Source: "ARCHITECTURE_DIAGRAM.md"; DestDir: "{app}\docs"; Flags: ignoreversion
Source: "LICENSE"; DestDir: "{app}\docs"; Flags: ignoreversion
Source: "docs\*"; DestDir: "{app}\docs"; Flags: ignoreversion recursesubdirs createallsubdirs; Tasks:

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{#MyAppName} CLI"; Filename: "{app}\cli\{#MyAppCLIName}"
Name: "{group}\Documentation"; Filename: "{app}\docs\README.md"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Registry]
; Add CLI to PATH
Root: HKCU; Subkey: "Environment"; ValueType: expandsz; ValueName: "Path"; ValueData: "{olddata};{app}\cli"; Check: NeedsAddPath('{app}\cli')

[Code]
function NeedsAddPath(Param: string): boolean;
var
  OrigPath: string;
begin
  if not RegQueryStringValue(HKEY_CURRENT_USER, 'Environment', 'Path', OrigPath) then
  begin
    Result := True;
    exit;
  end;
  Result := Pos(';' + Param + ';', ';' + OrigPath + ';') = 0;
end;

[Messages]
WelcomeLabel2=This will install [name/ver] on your computer.%n%nFileSync is a cloud storage deduplication system with importance-based tiering, client-side encryption, and automated redundancy management.%n%nIt is recommended that you close all other applications before continuing.
