# bash completion for devos
_devos() {
  local cur prev; cur="${COMP_WORDS[COMP_CWORD]}"; prev="${COMP_WORDS[COMP_CWORD-1]}"
  local cmds="doctor profile drift update tools --version --help"
  local pcmds="list inspect validate apply remove lock rollback"
  case "${COMP_WORDS[1]}" in
    profile) COMPREPLY=($(compgen -W "$pcmds" -- "$cur")); return;;
    drift)   COMPREPLY=($(compgen -W "check" -- "$cur")); return;;
    tools)   COMPREPLY=($(compgen -W "list" -- "$cur")); return;;
  esac
  COMPREPLY=($(compgen -W "$cmds" -- "$cur"))
}
complete -F _devos devos
