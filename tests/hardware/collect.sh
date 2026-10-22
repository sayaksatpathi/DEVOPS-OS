#!/usr/bin/env bash
# Hardware validation collector (gap #6). Run this ON a real DevOS machine (installed in a
# disposable setup, never your only disk) to gather a hardware-compatibility matrix row.
# The TEST is you using the machine; this tool records the evidence. No hardware QA can be
# done in CI — this is the code part; a human with physical hardware does the rest.
set -uo pipefail
echo "# DevOS hardware report — $(date -u +%FT%TZ)"
echo
echo "## System"
echo "- model: $(cat /sys/class/dmi/id/product_name 2>/dev/null || echo '?') / $(cat /sys/class/dmi/id/sys_vendor 2>/dev/null || echo '?')"
echo "- firmware: $(cat /sys/class/dmi/id/bios_version 2>/dev/null || echo '?')"
echo "- kernel: $(uname -r)"
echo "- os: $(. /etc/os-release 2>/dev/null; echo "$PRETTY_NAME")"
echo "- devos: $(cat /etc/devos-release 2>/dev/null || echo 'n/a')"
echo
echo "## Secure Boot"
echo "- $(mokutil --sb-state 2>/dev/null || echo 'mokutil not available')"
echo
echo "## CPU / memory"
echo "- cpu: $(grep -m1 'model name' /proc/cpuinfo | cut -d: -f2- | xargs 2>/dev/null)"
echo "- mem: $(free -h 2>/dev/null | awk '/Mem:/{print $2}')"
echo
echo "## Graphics / display"
lspci -nnk 2>/dev/null | grep -A2 -iE "vga|3d|display" | sed 's/^/- /'
echo
echo "## Network (Wi-Fi / Ethernet)"
lspci -nnk 2>/dev/null | grep -A2 -iE "network|ethernet" | sed 's/^/- /'
rfkill list 2>/dev/null | sed 's/^/- /'
echo
echo "## Audio"
lspci -nnk 2>/dev/null | grep -A2 -iE "audio" | sed 's/^/- /'
echo
echo "## Power / battery (laptops)"
if [ -d /sys/class/power_supply/BAT0 ]; then
  echo "- battery present: $(cat /sys/class/power_supply/BAT0/status 2>/dev/null)"
else
  echo "- no battery (desktop/VM)"
fi
echo
echo "## Suspend/resume — MANUAL: run 'systemctl suspend', resume, then note result here:"
echo "- suspend/resume: [ ] works  [ ] fails  notes: ____"
echo
echo "## Fill in and submit as a matrix row in docs/hardware-compatibility.md (redact serials)."
