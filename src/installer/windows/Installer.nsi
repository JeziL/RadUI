!include MUI2.nsh
!include FileFunc.nsh

;--------------------------------
;Icon

!define MUI_ICON "InstallerLogo.ico"

;--------------------------------
;Perform Machine-level install, if possible

!define MULTIUSER_EXECUTIONLEVEL Highest
;Add support for command-line args that let uninstaller know whether to
;uninstall machine- or user installation:
!define MULTIUSER_INSTALLMODE_COMMANDLINE
!include MultiUser.nsh
!include LogicLib.nsh

Function .onInit
  !insertmacro MULTIUSER_INIT
  ;Do not use InstallDir at all so we can detect empty $InstDir!
  ${If} $InstDir == "" ; /D not used
      ${If} $MultiUser.InstallMode == "AllUsers"
          StrCpy $InstDir "$PROGRAMFILES\RadUI"
      ${Else}
          StrCpy $InstDir "$LOCALAPPDATA\RadUI"
      ${EndIf}
  ${EndIf}
FunctionEnd

Function un.onInit
  !insertmacro MULTIUSER_UNINIT
FunctionEnd

;--------------------------------
;General

  Name "RadUI"
  OutFile "..\RadUISetup.exe"
  BrandingText "RadUI (c) 2019 Wang Jinli."

;--------------------------------
;Interface Settings

  !define MUI_ABORTWARNING

;--------------------------------
;Pages

  !define MUI_WELCOMEPAGE_TEXT "此向导将帮助您安装 RadUI。$\r$\n$\r$\n$\r$\n点击「下一步」以继续。"
  !insertmacro MUI_PAGE_WELCOME
  !insertmacro MUI_PAGE_DIRECTORY
  !insertmacro MUI_PAGE_INSTFILES
    !define MUI_FINISHPAGE_NOAUTOCLOSE
    !define MUI_FINISHPAGE_RUN
    !define MUI_FINISHPAGE_RUN_CHECKED
    !define MUI_FINISHPAGE_RUN_TEXT "运行 RadUI"
    !define MUI_FINISHPAGE_RUN_FUNCTION "LaunchLink"
    !define MUI_FINISHPAGE_SHOWREADME
    !define MUI_FINISHPAGE_SHOWREADME_FUNCTION "AddToContextMenu"
    !define MUI_FINISHPAGE_SHOWREADME_TEXT "将 RadUI 添加至右键菜单"
  !insertmacro MUI_PAGE_FINISH

  !insertmacro MUI_UNPAGE_CONFIRM
  !insertmacro MUI_UNPAGE_INSTFILES

;--------------------------------
;Languages

  !insertmacro MUI_LANGUAGE "SimpChinese"
  !insertmacro MUI_LANGUAGE "English"

;--------------------------------
;Installer Sections

!define UNINST_KEY \
  "Software\Microsoft\Windows\CurrentVersion\Uninstall\RadUI"
Section
  SetOutPath "$InstDir"
  File /r "..\RadUI\*"
  WriteRegStr SHCTX "Software\RadUI" "" $InstDir
  WriteUninstaller "$InstDir\uninstall.exe"
  CreateShortCut "$SMPROGRAMS\RadUI.lnk" "$InstDir\RadUI.exe"
  WriteRegStr SHCTX "${UNINST_KEY}" "DisplayName" "RadUI"
  WriteRegStr SHCTX "${UNINST_KEY}" "UninstallString" \
    "$\"$InstDir\uninstall.exe$\" /$MultiUser.InstallMode"
  WriteRegStr SHCTX "${UNINST_KEY}" "QuietUninstallString" \
    "$\"$InstDir\uninstall.exe$\" /$MultiUser.InstallMode /S"
  WriteRegStr SHCTX "${UNINST_KEY}" "Publisher" "Wang Jinli"
  ${GetSize} "$InstDir" "/S=0K" $0 $1 $2
  IntFmt $0 "0x%08X" $0
  WriteRegDWORD SHCTX "${UNINST_KEY}" "EstimatedSize" "$0"

SectionEnd

;--------------------------------
;Uninstaller Section

Section "Uninstall"

  RMDir /r "$InstDir"
  Delete "$SMPROGRAMS\RadUI.lnk"
  DeleteRegKey /ifempty SHCTX "Software\RadUI"
  DeleteRegKey HKCR "*\shell\RadUI"
  DeleteRegKey SHCTX "${UNINST_KEY}"

SectionEnd

Function LaunchLink
  !addplugindir "."
  ShellExecAsUser::ShellExecAsUser "open" "$SMPROGRAMS\RadUI.lnk"
FunctionEnd

Function AddToContextMenu
  WriteRegExpandStr HKCR "*\shell\RadUI" "" "Open with RadUI"
  WriteRegExpandStr HKCR "*\shell\RadUI" "Icon" "$InstDir\RadUI.exe"
  WriteRegExpandStr HKCR "*\shell\RadUI\command" "" "$\"$InstDir\RadUI.exe$\" $\"%1$\""
FunctionEnd