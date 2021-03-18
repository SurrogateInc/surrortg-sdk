#!/bin/bash
set -e

SCRIPT_PATH=$(dirname `which $0`)

cd $SCRIPT_PATH

# remove old modules
rm -rf source/modules
mkdir source/modules

# insert ninswitch README
cp ../games/ninswitch/README.md source/modules/ninswitch.md

# run apidoc
sphinx-apidoc -o source/modules/ --templatedir source/apidoc_templates/  --no-toc --no-headings --maxdepth 1 ../surrortg
sphinx-apidoc -o source/modules/ --templatedir source/example_templates/ --tocfile game_templates --no-headings --maxdepth 1 ../game_templates
# change the apidoc title with sed
sed -i '1s/surrortg/SDK reference/' source/modules/surrortg.rst
sed -i '2s/========/=============/' source/modules/surrortg.rst

# change the apidoc title with sed
sed -i '1s/game_templates/Template reference (IN DEVELOPMENT)/' source/modules/game_templates.rst
sed -i '2s/========/===================================/' source/modules/game_templates.rst

make clean
make html

if [ "$1" == "-s" ];
    then python -m http.server -d build/html/
elif [ "$1" == "-c" ];
    then chromium-browser build/html/index.html
elif [ "$1" == "-f" ];
    then firefox build/html/index.html
fi