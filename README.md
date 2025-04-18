# Chipflow Examples

## Install Requirements

Install the latest version of Python installed [Python Downloads](https://www.python.org/downloads/)
Ensure you have git command line tools installed [Git Downloads](https://git-scm.com/downloads)
We reccomend VS Code as a development environment [VSCode Downloads](https://code.visualstudio.com/download)
Github Desktop is a great tool for cloning git repos [Github Desktop Downloads](https://desktop.github.com/download/)

## Clone this repository

If you're familiar with git command line then you'll know what to do, otherwise use github desktop. Click the green 'Code' button at the top of this page and then 'Open with Github Desktop'. Once Github Desktop has cloned your repo you can click the button to open it in VSCode.

## Install the dependancies

In VScode, open up a terminal from the title menu bar.

We use pdm to manage our dependancies, so this will need to be installed. On the command line run `pip3 install pdm` to install it. Once this has completed, run `pdm install` to install the dependancies.


## VS Code debugger

* Download the [latest VSIX package](https://github.com/ChipFlow/rtl-debugger/releases/tag/latest) for the extension.
* Install it (eg `code --install-extension ../rtl-debugger-0.0.0.vsix` or right-click in explorer pane and select "Install VSIX").
* `Shift+Ctrl+P` "RTL Debugger: Start Session"
* `Shift+Ctrl+P` "RTL Debugger: Run Simulation Until..." "10ms"
* `Shift+Ctrl+P` "RTL Debugger: Go to Time..." "10ms"
