[Setup]
AppName=Chessli
AppVersion=1.1
DefaultDirName={pf}\Chessli
DefaultGroupName=Chessli
OutputDir=.
OutputBaseFilename=ChessliSetup1.1
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin

[Files]
Source: "Chessli.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "python-3.11.5-amd64.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall
Source: "pgn\Analysis_PGNs\*"; DestDir: "{app}\pgn\Analysis_PGNs"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "pgn\HumanVSEngine_PGNs\*"; DestDir: "{app}\pgn\HumanVSEngine_PGNs"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "pgn\EngineVSEngine_PGNs\*"; DestDir: "{app}\pgn\EngineVSEngine_PGNs"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Chessli"; Filename: "{app}\Chessli.exe"
Name: "{group}\{cm:UninstallProgram,ChessBot}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\Chessli"; Filename: "{app}\Chessli.exe"

[Run]
Filename: "{tmp}\python-3.11.5-amd64.exe"; Parameters: "/quiet InstallAllUsers=1 PrependPath=1"; Flags: waituntilterminated
Filename: "{app}\Chessli.exe"; Description: "{cm:LaunchProgram,ChessBot}"; Flags: nowait postinstall skipifsilent runascurrentuser
