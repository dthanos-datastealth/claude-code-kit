# Staging notice

This directory is a **complete standalone project staged inside
`claude-code-kit`**, not a part of the kit.

It belongs in its own repository -- `dthanos-datastealth/agentic-confidential-computing`
-- which could not be created during the session that produced it:
`create_repository` against the `dthanos-datastealth` organization returned 404,
and `add_repo` was never approved. It is staged here because the session's
container is ephemeral and this branch was the only writable destination.

To move it into its own repository:

```sh
mkdir agentic-confidential-computing && cd $_
# copy this directory's contents (minus this file), then
git init && git add -A && git commit
git remote add origin <new-repo-url> && git push -u origin main
```

Then delete this directory from `claude-code-kit`.

The kit's CI is unaffected: it triggers on `main` and pull requests, and its
pytest invocation is scoped to the root `tests/` directory.
