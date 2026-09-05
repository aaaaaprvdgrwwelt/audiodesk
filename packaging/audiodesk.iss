; Inno Setup: baut aus der PyInstaller-Ausgabe einen Windows-Installer.
;
; Aufruf (der Workflow macht das selbst):
;   iscc /DVersion=0.1.0 packaging\audiodesk.iss
;
; Bewusst eine Installation ohne Administratorrechte: sie landet unter
; %LOCALAPPDATA%. Das erspart die Nachfrage der Benutzerkontensteuerung,
; die bei einer unsignierten Datei ohnehin nach dem Herausgeber fragt und
; "Unbekannt" anzeigt.

#ifndef Version
  #define Version "0.0.0"
#endif

#define AppName "AudioDesk"
#define AppPublisher "AudioDesk"
#define AppURL "https://github.com/aaaaaprvdgrwwelt/audiodesk"

[Setup]
AppId={{9B4E6F31-2D87-4A6C-8F19-5A3C7E1B6D48}
AppName={#AppName}
AppVersion={#Version}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}/issues
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=..\dist
OutputBaseFilename=AudioDesk-{#Version}-Windows-Setup
SetupIconFile=audiodesk.ico
UninstallDisplayIcon={app}\AudioDesk.exe
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "deutsch"; MessagesFile: "compiler:Languages\German.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; \
  GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\AudioDesk\*"; DestDir: "{app}"; \
  Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\AudioDesk.exe"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\AudioDesk.exe"; \
  Tasks: desktopicon

[Run]
Filename: "{app}\AudioDesk.exe"; \
  Description: "{cm:LaunchProgram,{#AppName}}"; \
  Flags: nowait postinstall skipifsilent
