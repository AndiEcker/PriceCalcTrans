PriceCalcTrans
==============

Price Calculation Lua Script Transformer for SiHOT PMS


CD/SIHot Price Calculation Rules Lua Script Transformer
=======================================================

This add-on is helping SIHOT users to define and maintain flexible rules for room price calculations, done with lua scripts.

It consists of two parts:

(A) an AutoHotKey script (uigrabber.ahk) acting as an interface between the SIHOT application and the second part (B) of this add-on.
(B) a windows executable (PriceCalcTrans.exe) that is displaying the price calculation rules and allows to edit them.

Pressing the key combination Alt+Ctrl+Shift+P on a selected lua script editor tab in the Packages window of the SIHOT application is starting the AutoHotKey script (A).
The script first captures the content of the lua script from SIHOT, then starts the application (B) passing the lua script to it.
The application (B) is transforming the logic of the lua script into a set of rules and allows to create, edit and delete these rules.
Changed rulesets are transformed back to a lua script by the terminating application (B) and then passed back to the AutoHotKey script (A).
Finally the ahk script (A) is passing the changed lua script back into the lua script editor of the SIHOT application.


**** Installation ****

On the file server:
- Create a new folder on the server with full access for all users. Best map it to a drive, e.g. U:.
- Copy the AutoHotKey script (uigrabber.ahk) and the directory PCLT into the new folder.

On each local workstation:
- From http://l.autohotkey.net/AutoHotkey_L_Install.exe download and install AutoHotKey.
- Create a new windows startup entry with a command line for to load and activate the AutoHotkey script, e.g.:
     "C:\Program Files\AutoHotkey\AutoHotkey.exe" "U:\..path..to..\uigrabber.ahk"


**** Configuration ****

The configuration of this add-on can be done by editing the AutoHotkey script uagrabber.ahk.

The hotkey can be changed in the ahk script to any other key combination. The current hotkey is represented by the string '!^+p' in line 2 of the script. It is even possible to trigger the script run with mouse gestures.

The default folder structure of the installation directory and the used folder for to pass the lua script file from (A) to (B) and backwards can also be changed within the uigrabber.ahk script code.

If other applications or add-ons on the local workstation are already using AutoHotkey then simply merge the content of uigrabber.ahk into the existing AutoHotkey.ahk master script.

More info about AutoHotKey you find at http://www.autohotkey.com/.


**** Rule Definition ****

Each lua script is representing one ruleset. Within a ruleset the rules are ordered by priority (first 1, then 2, and so on ...). 

A rule consists of a name, a activated flag and one or more conditions and actions.

In the calculation process of daily room price the ruleset get processed by this priority, starting with rule 1 while skipping rules that are not activated. First the conditions of a rule get evaluated. 
If only one of the conditions of a rule is not fulfilled (is False) then the rule will be skipped and the conditions of the next activated rule will be evaluated.
If all the conditions of a rule are fulfilled than the actions of this rule get processed in order to determine the room price and the price finding/calculation process is terminated (no further rules get evaluated).


**** Condition And Action Types ****

The condition types allow to define number ranges for the length of stay and date ranges for arrival, staying (full stay) and selling dates - for to be evaluated against the values of a reservation.

The action types allow to set the values of discount percentages, promo codes, channel, NN1 and free days for a reservation - finally processed by the lua script within SIHOT.


**** User Interface ****

The ruleset is represented by the screen list in the top left area of the application window. Underneath are shown another two lists with the conditions and the actions of the currentlhy selected rule. Most of the changes can be done directly in the list, e.g. by clicking on the name of the rule a text line editor is coming up for to change the rule name. Please note to leave any formatting characters of formatted fields untouched, e.g. within date range entry fields don't delete any separation characters (neither the separators between month and year nor between the start and the end date). Other changes to the ruleset can be done with the buttons in the right area of the window, e.g. moving rules up and down in the list to change their priority of evaluation or for to add or delete rules, conditions and actions.

Changes to the ruleset will only be passed back to SIHOT by clicking the Modify button in the top right corner of the window. If you close the application with the window close box or the Cancel button then the changes you did to the ruleset will be lost!


**** Future Enhancements ****

- best price calculation (subset of rules can be marked to evaluate the best price - ignoring the rule priority - would need more input parameters from the SIHOT application to be passed into the lua script in order to calculate total stay price minimum).
- extend rule with accumulation flag (price finding process not terminates on rules with this flag set and the current action values get merged with the next rule where the conditions are matching).
- multi-language support (i18n).
- dynamic condition and action types (currently the type of conditions and actions are hard-coded but could be passed into a INI file in order to allow the definition of new condition and action types dynamically).
- more configuration settings (e.g. promo codes for list box section, default ranges, Res Channels/NN/.. codes, ...).
- UI enhancements: cancel app warning message, console debug messages, resizing and ui state restoring, ... please bare with me - this is my first Qt ;-)

<EOF>
