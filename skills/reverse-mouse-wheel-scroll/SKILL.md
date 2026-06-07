---
name: reverse-mouse-wheel-scroll
description: Reverse or restore Windows mouse wheel scrolling by setting FlipFlopWheel for present mouse devices. Use this skill whenever the user asks to reverse mouse wheel scroll, enable natural scrolling like macOS, restore Windows default scrolling, change mouse wheel direction, or mentions FlipFlopWheel on Windows.
---

# Reverse Mouse Wheel Scroll

Use this skill to change Windows mouse wheel direction for the current machine. Prefer automatic execution over interactive questions when the user's intent is clear.

The setting lives under each present mouse device:

`HKLM:\SYSTEM\CurrentControlSet\Enum\<device-id>\Device Parameters\FlipFlopWheel`

Values:
- `0`: Windows default scrolling. Downward wheel motion moves the page up so contents below appear.
- `1`: Natural scrolling like macOS. Downward wheel motion moves the page down so contents above appear.

Changing `HKLM` device registry values requires Administrator permission. The bundled script will relaunch itself with `Start-Process -Verb RunAs` if the current shell is not elevated.

## Workflow

1. Infer the intended mode from the user's request:
   - "开启 鼠标Mac 自然滚动", "开启鼠标 Mac 自然滚动", "enable natural scrolling", "reverse", "natural", "Mac", "macOS-like" -> `Natural`
   - "restore", "default", "Windows default", "undo reverse", "恢复默认滚动" -> `Default`
2. Do not ask an interactive confirmation question when the requested mode is clear. Execute the matching mode directly.
3. Only ask a short clarification if the user mentions changing mouse scrolling but does not indicate whether they want `Natural` or `Default`.
4. Run the bundled script from this skill:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Users\kamus\.axon\repo\skills\reverse-mouse-wheel-scroll\scripts\Set-ReverseMouseWheel.ps1" -Mode Natural
```

or:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Users\kamus\.axon\repo\skills\reverse-mouse-wheel-scroll\scripts\Set-ReverseMouseWheel.ps1" -Mode Default
```

5. Report the device names changed and the resulting `FlipFlopWheel` value.
6. Tell the user that Windows may require a restart, sign out/sign in, or reconnecting the mouse before the new direction is applied. For the user's usual workflow, specifically remind them to restart the computer.

## Verification

After running the script, verify by checking the script output. A successful run prints one row per mouse device with:

- `DeviceName`
- `InstanceId`
- `FlipFlopWheel`
- `Mode`

If no mouse devices are found, say that no present `Mouse` PnP devices with status `OK` were detected.

## Source

This workflow is based on the user's gist:

https://gist.github.com/kamusis/76fb48dc451c833a6b76dabfed766cef
