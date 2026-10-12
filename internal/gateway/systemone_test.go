package gateway

import (
	"bytes"
	"context"
	"io"
	"testing"

	"opencode2api/internal/identity"
	wire "opencode2api/internal/protocol"
)

func TestSystemOneUpstreamRequestUsesNativeEndpointAndPreservesBody(t *testing.T) {
	body := []byte(`{"model":"jev-1.13-free","state":{"ticket":"refund"},"questions":{"urgent":{"type":"noul","instructions":"Is it urgent?"}},"extension":{"keep":true}}`)
	ids := identity.RequestIDs{
		Session: "ses_test",
		Request: "req_test",
		Project: "prj_test",
	}

	req, err := newUpstreamRequest(context.Background(), "https://opencode.ai/zen", wire.SystemOne, body, ids, "public")
	if err != nil {
		t.Fatalf("newUpstreamRequest() error = %v", err)
	}
	if got, want := req.Method, "POST"; got != want {
		t.Errorf("request method = %q, want %q", got, want)
	}
	if got, want := req.URL.String(), "https://opencode.ai/zen/v1/systemone"; got != want {
		t.Errorf("request URL = %q, want %q", got, want)
	}
	if got, want := req.Header.Get("Authorization"), "Bearer public"; got != want {
		t.Errorf("Authorization = %q, want %q", got, want)
	}

	gotBody, err := io.ReadAll(req.Body)
	if err != nil {
		t.Fatalf("read request body: %v", err)
	}
	if !bytes.Equal(gotBody, body) {
		t.Errorf("System One request body was modified: got %s, want %s", gotBody, body)
	}
}

func TestPrepareAnonymousSystemOneBodyIsVerbatim(t *testing.T) {
	body := []byte(`{"model":"jev-1.13-free","state":"1 + 1 = 2","questions":{"q":{"type":"noul","instructions":"Is it true?"}}}`)
	got := prepareAnonymousBody(body, wire.SystemOne)
	if !bytes.Equal(got, body) {
		t.Errorf("anonymous System One body was modified: got %s, want %s", got, body)
	}
}
