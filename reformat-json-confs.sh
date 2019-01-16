#!/bin/bash
TMP=/tmp/fuuuu.json
for i in confs/*/*.json ; do
    node formatjson.js < $i > $TMP && cp $TMP $i
    rm $TMP
done