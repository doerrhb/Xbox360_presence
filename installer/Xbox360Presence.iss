#define MyAppName "Xbox360 Presence"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Xbox360 Presence"
#define MyAppExeName "Xbox360Presence.exe"

[Setup]
AppId={{97F0DCAB-1248-43F8-8EB2-9C3CFB070E3D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\dist\installer
OutputBaseFilename=Xbox360PresenceSetup
SetupIconFile=..\avatar.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}

[Tasks]
Name: "startup"; Description: "Start Xbox360 Presence when I sign in"; GroupDescription: "Windows startup:"; Flags: checkedonce
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; Flags: unchecked

[Files]
Source: "..\dist\Xbox360Presence.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Xbox360 Presence"; Filename: "{app}\{#MyAppExeName}"
Name: "{commondesktop}\Xbox360 Presence"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
Root: HKLM; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "Xbox360Presence"; ValueData: """{app}\{#MyAppExeName}"""; Flags: uninsdeletevalue; Tasks: startup

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent runasoriginaluser
