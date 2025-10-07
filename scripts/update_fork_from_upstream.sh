#!/bin/bash

# Fetch all updates from the upstream repository
git fetch --all

# Loop through all local branches
for branch in $(git branch --format='%(refname:short)')
do
  echo "Updating branch: $branch"

  # Checkout the branch
  git checkout "$branch"

  # Pull changes from upstream branch if it exists
  upstream=$(git rev-parse --abbrev-ref "$branch@{upstream}" 2>/dev/null)
  if [ -n "$upstream" ]; then
    git pull --ff-only
  else
    echo "  No upstream branch configured for $branch"
  fi
done

# Return to original branch
git checkout -

echo "All branches updated!"
