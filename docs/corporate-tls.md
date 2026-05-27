# Corporate TLS

This guide describes how to use the kit on a machine behind a corporate
TLS-intercepting proxy — the kind that re-signs HTTPS traffic with an
internal certificate authority so that security tooling can inspect the
contents in transit.

The kit makes no employer- or vendor-specific assumptions about your
environment; the steps below are generic. If your IT team publishes their
own configuration documentation, prefer theirs for the parts that overlap.

---

## 1. Obtain your corporate CA bundle

Ask your IT or platform team for the corporate root CA certificate (and
any intermediates) in PEM format. The file is usually distributed as a
single `.pem` or `.crt` file containing one or more
`-----BEGIN CERTIFICATE-----` blocks.

For DER format (`.cer`, `.der`), convert to PEM with
`openssl x509 -inform der -in corporate-ca.cer -out corporate-ca.pem`.
For a multi-cert chain in a single file, concatenate the PEM blocks in
order (root last) with `cat intermediate.pem root.pem > corporate-ca.pem`.

---

## 2. Where to put it

Pick a stable, user-owned location and use it consistently. Either of
these works:

- `~/.config/claude-code-kit/corporate-ca.pem` — follows the
  XDG-style convention; appropriate if you want the file scoped to the
  kit.
- `~/.claude/certs/corporate-ca.pem` — lives alongside the other
  Claude Code configuration; appropriate if you want the bundle reused
  by other Claude-specific tooling.

Create the directory and copy the file in:

```sh
mkdir -p ~/.config/claude-code-kit
cp /path/to/corporate-ca.pem ~/.config/claude-code-kit/corporate-ca.pem
chmod 600 ~/.config/claude-code-kit/corporate-ca.pem
```

The rest of this guide uses `~/.config/claude-code-kit/corporate-ca.pem`
in the examples; substitute your chosen path consistently.

---

## 3. Environment variables to export

Different layers of the stack read different environment variables for
the CA bundle. The kit's tools span all of these layers, so set every
variable that applies to a tool you actually use.

| Variable              | Layer                       | Affects                                                                 |
|-----------------------|-----------------------------|-------------------------------------------------------------------------|
| `SSL_CERT_FILE`       | OpenSSL                     | `curl`, `uv`'s downloads, most CLIs linked against system OpenSSL.      |
| `REQUESTS_CA_BUNDLE`  | Python `requests`           | Anything in the kit that uses Python `requests` (some skills, lints).   |
| `GIT_SSL_CAINFO`      | `git` (libcurl)             | `git clone`, `git push`, `git fetch` against HTTPS remotes.             |
| `NODE_EXTRA_CA_CERTS` | Node.js TLS                 | Node-based MCP servers, `gh` extensions implemented in Node, npm.       |

Set them in your current shell:

```sh
export SSL_CERT_FILE="$HOME/.config/claude-code-kit/corporate-ca.pem"
export REQUESTS_CA_BUNDLE="$HOME/.config/claude-code-kit/corporate-ca.pem"
export GIT_SSL_CAINFO="$HOME/.config/claude-code-kit/corporate-ca.pem"
export NODE_EXTRA_CA_CERTS="$HOME/.config/claude-code-kit/corporate-ca.pem"
```

Notes:

- These variables expect a single PEM file path (or, for some
  implementations, a directory of PEM files). Use the path to the bundle
  you assembled in step 1.
- `SSL_CERT_FILE` is widely respected; `SSL_CERT_DIR` is the directory
  equivalent. If your OpenSSL is configured for a directory of hashed
  symlinks, that is also valid but is less portable.
- `NODE_EXTRA_CA_CERTS` *adds* certificates to Node's default trust
  store rather than replacing it. Most other variables *replace* the
  default trust store with the file you point them at — make sure your
  corporate bundle includes the root CAs you still need (Mozilla CA
  list, etc.) or that the proxy re-signs traffic to those upstreams.

---

## 4. Make it persistent (shell-rc snippet)

To avoid re-exporting the variables in every shell, add the snippet to
your shell's startup file (`~/.zshrc`, `~/.bashrc`, or equivalent):

```sh
# --- Corporate TLS-intercepting proxy: trust the internal CA ---
CCK_CA="$HOME/.config/claude-code-kit/corporate-ca.pem"
if [ -f "$CCK_CA" ]; then
  export SSL_CERT_FILE="$CCK_CA"
  export REQUESTS_CA_BUNDLE="$CCK_CA"
  export GIT_SSL_CAINFO="$CCK_CA"
  export NODE_EXTRA_CA_CERTS="$CCK_CA"
fi
unset CCK_CA
```

The `if [ -f "$CCK_CA" ]` guard means the snippet is safe to commit to a
dotfiles repo: machines without the bundle skip the export silently
rather than breaking shell startup.

Reload your shell (`exec $SHELL -l`) or open a new terminal to pick up
the changes.

---

## 5. Per-command override (one-off use)

For one-off installs where you do not want to modify your shell-rc — for
example, on a machine where you are about to revert the change — set
the variable inline for a single command:

```sh
SSL_CERT_FILE="$HOME/.config/claude-code-kit/corporate-ca.pem" \
  uv tool install some-package

GIT_SSL_CAINFO="$HOME/.config/claude-code-kit/corporate-ca.pem" \
  git clone https://github.com/owner/repo

NODE_EXTRA_CA_CERTS="$HOME/.config/claude-code-kit/corporate-ca.pem" \
  npm install -g typescript-language-server
```

This pattern is also useful when debugging — if a one-off command
succeeds with the override but the persistent export is set, the
problem is upstream of the env var (e.g. the tool reads a different
variable, or it bundles its own trust store).

---

## 6. Verification

Verify that the OpenSSL layer trusts your proxy:

```sh
curl -v https://api.github.com 2>&1 | grep "SSL certificate"
```

A trusted connection prints a line like `SSL certificate verify ok`.
An untrusted one prints `SSL certificate problem: unable to get local
issuer certificate` or similar.

If `curl` reports OK but a tool still fails, the tool is reading a
different env var or bundling its own trust store. Check:

- `python3 -c "import ssl; print(ssl.get_default_verify_paths())"` —
  shows where Python's stdlib looks.
- `git config --get-all http.sslcainfo` — shows git's configured bundle
  (in addition to `GIT_SSL_CAINFO`).
- `node -e "console.log(process.env.NODE_EXTRA_CA_CERTS)"` — confirms
  Node sees the variable.

For per-tool diagnosis, run the tool with its verbose flag and look for
the certificate the tool is presenting (the corporate root) versus the
one it expected (the public root).

---

## 7. Common failure modes

- **`uv tool install` fails with TLS errors** — `uv` invokes its own
  downloads. Confirm `SSL_CERT_FILE` is set in the shell that ran it.
- **`git clone` works but a Node-based MCP fails** — Node has its own
  trust store. Set `NODE_EXTRA_CA_CERTS` and retry; subprocesses must
  also inherit the variable.
- **`install.sh` fails on plugin marketplace fetch** — the script
  shells out to `git` and `claude`; reload your rc with
  `exec $SHELL -l` and retry.
- **Intermittent failures on some hosts** — the proxy may exempt
  certain hostnames, returning the original cert chain. Bundle the
  public roots into your PEM file, or use `SSL_CERT_DIR` pointing at a
  directory containing both.

---

## 8. Removing the configuration

Remove the shell-rc snippet (or comment it out), delete the PEM file,
and `exec $SHELL -l`. The kit stores no trust configuration; everything
lives in env vars and the PEM file you control.

---

## Further reading

- [`docs/prereqs.md`](prereqs.md) — install steps for the kit's
  prerequisites, several of which fetch over HTTPS.
- [`docs/workflow.md`](workflow.md) — the development loop.
