# devos_ca — corporate CA trust (§5)

Makes the system CA bundle (`/etc/ssl/certs/ca-certificates.crt`) authoritative for Node,
Python, curl, git, and Rust via `/etc/profile.d/devos-ca.sh`. To trust a corporate CA:

```bash
sudo cp corp-root.crt /usr/local/share/ca-certificates/corp-root.crt
sudo update-ca-certificates
```

Or pass `devos_ca_certs: [path, ...]` to the role. Behind a TLS-inspecting proxy, this is
what makes package managers and language runtimes trust the proxy's CA.
