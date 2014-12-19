#! /bin/bash

for i in `find ./ | grep .py$`
do
  echo $i
  if ! grep -q Copyright $i
  then
    cat copyright.txt $i >$i.new && mv $i.new $i
  fi
done