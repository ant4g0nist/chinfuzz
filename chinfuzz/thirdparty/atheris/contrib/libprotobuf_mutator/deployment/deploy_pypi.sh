#!/bin/bash
# Copyright 2022 Google LLC
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

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "${DIR}/../"

# Validate args - dev or prod
pypi="$1"
if [ -z "$pypi" ]; then
  >&2 printf "$0 requires one argument, testpypi or pypi. Usage:\n\t$0 testpypi\n\t$0 pypi\n"
  exit 1
fi

# Verify that we're pushing a valid git state
git_status="$(git status --porcelain --ignored)"
if [[ ! -z "$git_status" ]]; then
  >&2 echo "Git working directory not clean - please ensure it's pristine before deploying (including any gitignored files)."
  exit 1
fi

(
  set -e -x
  # Build and push
  python3 setup.py sdist
  python3 -m twine upload --repository "$pypi" dist/*
)
