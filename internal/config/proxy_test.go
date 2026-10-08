package config

import (
	"net/http"
	"net/http/httptest"
	"reflect"
	"testing"
)

func TestResolveProxyFilesRemoteURL(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		_, _ = w.Write([]byte("http://127.0.0.1:8080\n\nhttps://127.0.0.1:8443 # comment\n"))
	}))
	defer server.Close()

	cfg := Config{ProxyFile: server.URL}
	if err := resolveProxyFiles("/tmp/config.json", &cfg); err != nil {
		t.Fatalf("resolveProxyFiles() error = %v", err)
	}

	want := []string{
		"http://127.0.0.1:8080",
		"https://127.0.0.1:8443",
	}
	if !reflect.DeepEqual(cfg.effectiveProxies, want) {
		t.Fatalf("effectiveProxies = %#v, want %#v", cfg.effectiveProxies, want)
	}
}

func TestReadProxyFileRemoteHTTPError(t *testing.T) {
	server := httptest.NewServer(http.NotFoundHandler())
	defer server.Close()

	_, err := readProxyFile(server.URL)
	if err == nil {
		t.Fatal("readProxyFile() error = nil, want HTTP error")
	}
}
