#!/bin/bash
set -e

SCRIPT_PATH=$(dirname `which $0`)

cd $SCRIPT_PATH

# install dependencies
# got from here: https://www.sphinx-doc.org/en/master/usage/builders/index.html#sphinx.builders.latex.LaTeXBuilder
sudo apt-get install texlive-latex-recommended texlive-fonts-recommended texlive-latex-extra latexmk

# build the pdf
make latexpdf

# open in browser
if [ "$1" == "-c" ];
    then chromium-browser build/latex/surrortgsdk.pdf
elif [ "$1" == "-f" ];
    then firefox build/latex/surrortgsdk.pdf
fi