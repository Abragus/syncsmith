alias ..="cd .."
alias ls='ls --color=auto'
alias ll="ls -alh"
alias ld="ls -ald */"
alias scl="systemctl"
alias jcl="journalctl -xeu"
alias updn="sudo dnf update -y; sudo flatpak update -y"

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

# Esek
export SSH_AUTH_SOCK="$HOME/.bitwarden-ssh-agent.sock"
