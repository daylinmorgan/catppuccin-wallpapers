update-assets:
  ./bin/update-assets

generate-assets:
  #!/usr/bin/env bash
  for src in $(find -path './src/*' -prune -type d); do
    ./generate-pngs.py $src
  done

