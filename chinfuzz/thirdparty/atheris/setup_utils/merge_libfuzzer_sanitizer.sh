#!/bin/bash
# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

set -e

libfuzzer="$1"
sanitizer="$2"
strip_preinit="$3"

tmpdir="$(mktemp -d)"
tmp_sanitizer="${tmpdir}/sanitizer.a"
tmp_merged="${tmpdir}/sanitizer.so"

if [ -z "$CXX" ]; then
  if which clang++ > /dev/null 2>&1; then
    export CXX="clang++"
  else
    export CXX="g++"
  fi
fi

cp "$sanitizer" "$tmp_sanitizer"

ar d "$tmp_sanitizer" $strip_preinit  # Intentionally not quoted

"$CXX" -Wl,--whole-archive "$libfuzzer" "$tmp_sanitizer" -Wl,--no-whole-archive -lpthread -ldl -shared -o "$tmp_merged"

echo "$tmp_merged"
exit 0
