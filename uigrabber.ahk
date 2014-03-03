;; test script activated with Alt+Ctrl+Shift+P
!^+p::
installPath = %A_ScriptDir%\PCLT
scriptFile = %A_Temp%\Lua%A_Now%%A_MSec%.txt

VarSetCapacity(scriptText, 65000)
ControlGetText, scriptText, Edit23, A     		; get lua from SIHOT (A=activeWin)
if (ErrorLevel <> 0)
{
    MsgBox, SIHOT lua script editor is not accessible. Please activate the SIHOT application and make sure that the lua script editor is visible.
    return
}

FileDelete, %scriptFile%
FileAppend, %scriptText%, %scriptFile%
scriptText = 

RunWait, %installPath%\PriceCalcTrans.exe %scriptFile%, %installPath%
if (ErrorLevel = 0)
{
    fileSize = 0
    FileGetSize, fileSize, %scriptFile%
    if (ErrorLevel <> 0)
    {
        MsgBox, % "Lua script file " . scriptFile . " is locked or does no longer exist!"
        return						; RETURN
    }
    if (fileSize <= 0)
    {
        MsgBox, % "Lua script file " . scriptFile . " is invalid or empty (Length=" . fileSize . " bytes)"
        return						; RETURN
    }

    FileRead, scriptText, %scriptFile%                  ; load script from file

    if (ErrorLevel <> 0)
    {
        MsgBox, % "Error " . ErrorLevel . " while loading lua script file " . scriptFile . "!"
    }
    else if (scriptText = "")
    {
        MsgBox, % "Content of lua script file " . scriptFile . " is empty."
    }
    else
    {
        ControlSetText, Edit23, %scriptText%, A         ; write script back to SIHOT application
        if (ErrorLevel <> 0)
        {
            MsgBox, Lua script editor was not accessible. Please next time while this application is open don't switch to other applications, including SIHOT.
        }
    }
}
return

