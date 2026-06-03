from aicm.backends import BACKENDS
from aicm.prompts import FORMATS


def bash_completion():
    backends = " ".join(BACKENDS.keys())
    formats = " ".join(FORMATS)
    return f'''_git_aicm() {{
    local cur prev commands opts
    COMPREPLY=()
    cur="${{COMP_WORDS[COMP_CWORD]}}"
    prev="${{COMP_WORDS[COMP_CWORD-1]}}"
    commands="setup config generate completions reinstall update"
    opts="--backend --model --ollama-url --profile --format --ticket --context --detailed --dry-run --version --help"

    case "$prev" in
        --backend)
            COMPREPLY=( $(compgen -W "{backends}" -- "$cur") )
            return 0
            ;;
        --format)
            COMPREPLY=( $(compgen -W "{formats}" -- "$cur") )
            return 0
            ;;
        --profile)
            COMPREPLY=( $(compgen -W "$(aws configure list-profiles 2>/dev/null)" -- "$cur") )
            return 0
            ;;
    esac

    if [[ $COMP_CWORD -eq 1 && "$cur" != -* ]]; then
        COMPREPLY=( $(compgen -W "$commands" -- "$cur") )
        return 0
    fi

    COMPREPLY=( $(compgen -W "$opts" -- "$cur") )
}}
complete -F _git_aicm git-aicm
'''


def zsh_completion():
    backends = " ".join(BACKENDS.keys())
    formats = " ".join(FORMATS)
    return f'''#compdef git-aicm

_git-aicm() {{
    local -a commands
    commands=(
        'setup:Interactive setup wizard'
        'config:View or set config values'
        'generate:Generate a commit message'
        'reinstall:Reset venv and reinstall'
        'update:Update to the latest version'
    )

    _arguments -C \\
        '--version[Show version]' \\
        '--help[Show help]' \\
        '--backend[LLM backend]:backend:({backends})' \\
        '--model[Model name]:model:' \\
        '--ollama-url[Ollama server URL]:url:' \\
        '--profile[AWS profile]:profile:_aws_profiles' \\
        '--format[Commit format]:format:({formats})' \\
        '--ticket[Ticket reference]:ticket:' \\
        '--context[Extra context for the AI]:context:' \\
        '--detailed[Include bullet points]' \\
        '--dry-run[Print without committing]' \\
        '1:command:->cmds' \\
        '*::arg:->args'

    case "$state" in
        cmds)
            _describe 'command' commands
            ;;
    esac
}}

_aws_profiles() {{
    local -a profiles
    profiles=(${{(f)"$(aws configure list-profiles 2>/dev/null)"}})
    _describe 'profile' profiles
}}

_git-aicm "$@"
'''


def cmd_completions(args):
    shell = args.shell
    if shell == "bash":
        print(bash_completion())
    elif shell == "zsh":
        print(zsh_completion())
