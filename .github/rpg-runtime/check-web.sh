#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../web"
npm run checkTypes --workspace=ruffle-core
npm run checkTypes --workspace=ruffle-selfhosted
npm test --workspace=ruffle-core
npx --no-install eslint \
  packages/core/src/internal/builder.ts \
  packages/core/src/internal/player/impl_v1.ts \
  packages/core/src/internal/player/inner.tsx \
  packages/core/src/public/config/default.ts \
  packages/core/src/public/config/load-options.ts \
  packages/core/src/public/player/v1.ts \
  packages/core/tools/set_version.ts \
  packages/core/tools/build_date.ts \
  packages/core/test/build_date.ts \
  packages/selfhosted/webpack.config.js
