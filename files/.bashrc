alias ..="cd .."
alias ls='ls --color=auto'
alias ll="ls -alh"
alias ld="ls -ald */"
alias scl="systemctl"
alias sclu="systemctl --user"
jcl() {
    journalctl -eu "$1" | less +G
}

jclu() {
    journalctl --user -eu "$1" | less +G
}
alias updn="sudo tmux new-session \"dnf update -y; read\" \; split-window -h \"flatpak update -y; read\""
alias cop="wl-copy"

git() {
  if [[ "$1" =~ ^(add|restore|commit|ci|push|pull)$ ]]; then
    command git "$@" && command git status
  else
    command git "$@"
  fi
}

new_line() {
    printf "\n> "
}

PROMPT_COMMAND='make_prompt'
make_prompt () {
    PS1="\[\033[95m\]\u@\h \[\033[36m\]\A \[\033[32m\]\w\[\033[33m\] "

    branch=$(git symbolic-ref --short HEAD 2>/dev/null)

    if [ -n "$branch" ]; then
        PS1+="[$branch] ";
    fi

    PS1+="\[\033[00m\]$(new_line)"
}

source ~/.git-completion.bash

export PATH=$PATH:/home/gustav/.local/bin

# Esek
export SSH_AUTH_SOCK="$HOME/.bitwarden-ssh-agent.sock"
