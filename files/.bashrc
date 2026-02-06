alias ..="cd .."
alias ls='ls --color=auto'
alias ll="ls -alh"
alias ld="ls -ald */"
alias scl="systemctl"
alias jcl="journalctl -xeu"

# if [ "$os" = "linux" ]; then
# #    function code() {
# #        (flatpak run --socket=wayland com.visualstudio.code --ozone-platform-hint=auto --enable-features=WaylandWindowDecorations $* > /dev/null 2>&1)
# #    }
#     # alias conNginx="sshfs gustav@10.0.1.21:/var/www/gustav-development.duckdns.org/ /home/gustav/gustav-development/"
#     # alias conHA="sshfs root@10.0.1.43:/config/ /home/gustav/homeassistant/"
#     # export PATH="/usr/bin/php:$PATH"
# fi

# alias HA="ssh 10.0.1.43 -l root"

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
