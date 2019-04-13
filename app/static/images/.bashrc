if ! pgrep ssh-agent > /dev/null; then
  ssh-agent > ~/.ssh-agent-thing
fi
if [[ "$SSH_AGENT_PID" == "" ]]; then
  eval $(<~/.ssh-agent-thing)
fi
ssh-add -l >/dev/null || alias ssh='ssh-add -l >/dev/null || ssh-add && unalias ssh; ssh'



clear && archey3 -c cyan 

if [ -f /etc/bash_completion ]; then
	    . /etc/bash_completion
fi

xhost +local:root > /dev/null 2>&1

complete -cf sudo

shopt -s cdspell
shopt -s checkwinsize
shopt -s cmdhist
shopt -s dotglob
shopt -s expand_aliases
shopt -s extglob
shopt -s histappend
shopt -s hostcomplete
shopt -s nocaseglob

export HISTSIZE=10000
export HISTFILESIZE=${HISTSIZE}
export HISTCONTROL=ignoreboth

alias ls='ls --group-directories-first --time-style=+"%d.%m.%Y %H:%M" --color=auto -F'
alias ll='ls -l --group-directories-first --time-style=+"%d.%m.%Y %H:%M" --color=auto -F'
alias la='ls -la --group-directories-first --time-style=+"%d.%m.%Y %H:%M" --color=auto -F'
alias grep='grep --color=tty -d skip'
alias cp="cp -i"                          # confirm before overwriting something
alias df='df -h'                          # human-readable sizes
alias free='free -m'                      # show sizes in MB
alias np='nano PKGBUILD'
alias clean='clear && archey3 -c cyan' 
alias c='clear'
alias h?="history | grep"
alias tv8='sudo systemctl start teamviewerd && teamviewer'
alias usb='sudo ls -l /dev/disk/by-id/'
alias shist='history | grep'
alias umounta='sudo umount -R /media'

alias pacu='packer -Syu'
alias pacs='packer'
alias paci='packer -S'
alias pacr='sudo pacman -Rsn'
alias chkup='pacman -Sy | echo && pacman -Qu | wc -l | figlet'

alias archpi='ssh nathan@192.168.1.40'
alias archtv='ssh nathan@192.168.1.41'
alias pachrpi='ping 192.168.1.40'
alias parchtv='ping 192.168.1.41'

alias apti='sudo apt-get install'
alias apts='apt-cache search'
alias aptre='sudo apt-get --reinstall install'
alias aptr='sudo apt-get'
alias zombies='echo $(( 1+RANDOM%54 )) | figlet'
alias items='echo $(( 1+RANDOM%88 )) | figlet'
alias dice='echo $(( 1+RANDOM%6 )) | figlet'

# Reset
# Color_Off='\e[0m'       # Text Reset

 # Regular Colors
 Black='\e[0;30m'        # Black
 Red='\e[0;31m'          # Red
 Green='\e[0;32m'        # Green
 Yellow='\e[0;33m'       # Yellow
 Blue='\e[0;34m'         # Blue
 Purple='\e[0;35m'       # Purple
 Cyan='\e[0;36m'         # Cyan
 White='\e[0;37m'        # White

 # Bold
 BBlack='\e[1;30m'       # Black
 BRed='\e[1;31m'         # Red
 BGreen='\e[1;32m'       # Green
 BYellow='\e[1;33m'      # Yellow
 BBlue='\e[1;34m'        # Blue
 BPurple='\e[1;35m'      # Purple
 BCyan='\e[1;36m'        # Cyan
 BWhite='\e[1;37m'       # White

 # Underline
 UBlack='\e[4;30m'       # Black
 URed='\e[4;31m'         # Red
 UGreen='\e[4;32m'       # Green
 UYellow='\e[4;33m'      # Yellow
 UBlue='\e[4;34m'        # Blue
 UPurple='\e[4;35m'      # Purple
 UCyan='\e[4;36m'        # Cyan
 UWhite='\e[4;37m'       # White

 # Background
 On_Black='\e[40m'       # Black
 On_Red='\e[41m'         # Red
 On_Green='\e[42m'       # Green
 On_Yellow='\e[43m'      # Yellow
 On_Blue='\e[44m'        # Blue
 On_Purple='\e[45m'      # Purple
 On_Cyan='\e[46m'        # Cyan
 On_White='\e[47m'       # White

 # High Intensity
 IBlack='\e[0;90m'       # Black
 IRed='\e[0;91m'         # Red
 IGreen='\e[0;92m'       # Green
 IYellow='\e[0;93m'      # Yellow
 IBlue='\e[0;94m'        # Blue
 IPurple='\e[0;95m'      # Purple
 ICyan='\e[0;96m'        # Cyan
 IWhite='\e[0;97m'       # White

 # Bold High Intensity
 BIBlack='\e[1;90m'      # Black
 BIRed='\e[1;91m'        # Red
 BIGreen='\e[1;92m'      # Green
 BIYellow='\e[1;93m'     # Yellow
 BIBlue='\e[1;94m'       # Blue
 BIPurple='\e[1;95m'     # Purple
 BICyan='\e[1;96m'       # Cyan
 BIWhite='\e[1;97m'      # White

 # High Intensity backgrounds
 On_IBlack='\e[0;100m'   # Black
 On_IRed='\e[0;101m'     # Red
 On_IGreen='\e[0;102m'   # Green
 On_IYellow='\e[0;103m'  # Yellow
 On_IBlue='\e[0;104m'    # Blue
 On_IPurple='\e[0;105m'  # Purple
 On_ICyan='\e[0;106m'    # Cyan
 On_IWhite='\e[0;107m'   # White


# ex - archive extractor
# usage: ex <file>
ex ()
{
  if [ -f $1 ] ; then
    case $1 in
      *.tar.bz2)   tar xjf $1   ;;
      *.tar.gz)    tar xzf $1   ;;
      *.bz2)       bunzip2 $1   ;;
      *.rar)       unrar x $1     ;;
      *.gz)        gunzip $1    ;;
      *.tar)       tar xf $1    ;;
      *.tbz2)      tar xjf $1   ;;
      *.tgz)       tar xzf $1   ;;
      *.zip)       unzip $1     ;;
      *.Z)         uncompress $1;;
      *.7z)        7z x $1      ;;
      *)           echo "'$1' cannot be extracted via ex()" ;;
    esac
  else
    echo "'$1' is not a valid file"
  fi
}


# prompt
PS1='\[\e[1;31m\]●\[\e[0m\] \h \[\e[1;33m\]\w\[\e[0m\] \[\e[1;32m\]>>\[\e[0m\] '
BROWSER=/usr/bin/xdg-open
EDITOR=vim
