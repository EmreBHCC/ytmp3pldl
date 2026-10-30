; Inno Setup 6. Surum derle.ps1'den gelir: ISCC /DSurum=<surum>
#ifndef Surum
  #define Surum "0.0.0"
#endif

[Setup]
AppId={{967E9B7A-B818-4AAA-9C57-8C7F48B3101E}
AppName=YouTube İndirici
AppVersion={#Surum}
AppVerName=YouTube İndirici {#Surum}
AppPublisher=Emre Bahçeci
AppPublisherURL=https://github.com/EmreBHCC/ytmp3pldl
DefaultDirName={localappdata}\Programs\ytmp3pldl
DisableProgramGroupPage=yes
DisableDirPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\dist
OutputBaseFilename=ytmp3pldl-kurulum-{#Surum}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayName=YouTube İndirici
UninstallDisplayIcon={app}\ytmp3pldl.exe
CloseApplications=yes

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"

[Tasks]
Name: "masaustu"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "..\dist\ytmp3pldl\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\YouTube İndirici"; Filename: "{app}\ytmp3pldl.exe"
Name: "{autodesktop}\YouTube İndirici"; Filename: "{app}\ytmp3pldl.exe"; Tasks: masaustu

[Run]
Filename: "{app}\ytmp3pldl.exe"; Description: "{cm:LaunchProgram,YouTube İndirici}"; Flags: nowait postinstall skipifsilent
