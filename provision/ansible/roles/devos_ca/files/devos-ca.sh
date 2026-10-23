# DevOS: point common language runtimes at the system CA trust store so a corporate CA
# added via `update-ca-certificates` is honored everywhere (§5 corporate-CA handling).
_devos_bundle=/etc/ssl/certs/ca-certificates.crt
if [ -r "$_devos_bundle" ]; then
  export NODE_EXTRA_CA_CERTS="$_devos_bundle"       # Node.js
  export REQUESTS_CA_BUNDLE="$_devos_bundle"        # Python requests
  export SSL_CERT_FILE="$_devos_bundle"             # OpenSSL/Python/curl
  export CURL_CA_BUNDLE="$_devos_bundle"            # curl
  export GIT_SSL_CAINFO="$_devos_bundle"            # git
  export CARGO_HTTP_CAINFO="$_devos_bundle"         # Rust cargo
fi
