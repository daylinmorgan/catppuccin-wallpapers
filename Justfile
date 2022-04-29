update-assets:
  ./bin/update-assets

generate-assets:
  #!/usr/bin/env bash
  for src in $(find -path './src/*' -prune -type d); do
    ./generate-pngs.py $src
  done

zip-assets:
  #!/usr/bin/env bash
  set -e

  git checkout assets || exit
  find pngs -mindepth 1 -maxdepth 1 -type d -execdir tar czvf ../{}.tar.gz {} \;
  tar czvf all.tar.gz pngs/*

