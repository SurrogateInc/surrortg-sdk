#!/bin/bash
SCRIPT_PATH=$(dirname `which $0`)

cd $SCRIPT_PATH
rm -rf source/modules
mkdir source/modules
sphinx-apidoc -o source/modules/ ../surrortg ../surrortg/lib ../surrortg/network --templatedir source/apidoc_templates/  --no-toc --no-headings --maxdepth 1

# change the apidoc title with sed
sed -i '1s/surrortg/SDK reference/' source/modules/surrortg.rst
sed -i '2s/========/============/' source/modules/surrortg.rst

make clean
make html

if [ "$1" == "-s" ];
    then python -m http.server -d build/html/
elif [ "$1" == "-c" ];
    then chromium-browser build/html/index.html
elif [ "$1" == "-f" ];
    then firefox build/html/index.html
fi