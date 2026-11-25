; Script de Inno Setup 6 para MuniCertificados
; Municipalidad de San Roque (Corrientes) — Área de Modernización y Redes

#define MyAppName "MuniCertificados — Municipalidad de San Roque"
#define MyAppShortName "MuniCertificados"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Municipalidad de San Roque — Área de Modernización y Redes"
#define MyAppExeName "MuniCertificados.exe"

[Setup]
AppId={{8F9D4A2C-5E1B-4C7A-9B3E-2D6F1A8C0E45}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} v{#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppShortName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
MinVersion=6.1sp1
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=dist_installer
OutputBaseFilename=Setup_MuniCertificados_v1.0
SetupIconFile=assets\app_icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "dist\MuniCertificados\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\MuniCertificados\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTA: Los datos del usuario, base de datos SQLite y certificados generados se guardan en
; Documentos\Muni_Certificados\ y se preservan intactos al actualizar o desinstalar la aplicación.

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{group}\Desinstalar {#MyAppShortName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppShortName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppShortName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
