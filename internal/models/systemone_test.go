package models

import (
	"context"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"opencode2api/internal/config"
	wire "opencode2api/internal/protocol"
)

func TestFetchProtocolDocsRoutesJevModelsThroughSystemOne(t *testing.T) {
	document := strings.Join([]string{
		"| Model | ID | Endpoint | SDK |",
		"| --- | --- | --- | --- |",
		"| Jev 1.13 | jev-1.13 | `https://opencode.ai/zen/v1/systemone` | - |",
		"| Jev 1.13 Free | jev-1.13-free | `https://opencode.ai/zen/v1/systemone` | - |",
		"| Space Bunny Free | space-bunny-free | `https://opencode.ai/zen/v1/chat/completions` | `@ai-sdk/openai-compatible` |",
	}, "\n")
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/markdown; charset=utf-8")
		_, _ = w.Write([]byte(document))
	}))
	defer server.Close()

	protocols, err := FetchProtocolDocs(context.Background(), server.Client(), server.URL)
	if err != nil {
		t.Fatalf("FetchProtocolDocs() error = %v", err)
	}
	for _, model := range []string{"jev-1.13", "jev-1.13-free"} {
		if got := protocols[model]; got != wire.SystemOne {
			t.Errorf("protocols[%q] = %q, want %q", model, got, wire.SystemOne)
		}
	}
	if got := protocols["space-bunny-free"]; got != wire.Chat {
		t.Errorf("protocols[%q] = %q, want %q", "space-bunny-free", got, wire.Chat)
	}

	catalog := NewCatalog(config.TierZen, nil)
	catalog.ReplaceWithCapabilities(
		[]string{"jev-1.13", "jev-1.13-free", "space-bunny-free"},
		[]string{},
		map[config.Tier]map[string]wire.Protocol{
			config.TierZen: protocols,
			config.TierGo:  map[string]wire.Protocol{},
		},
		nil,
		nil,
	)

	anonymousRoute, err := catalog.Route("jev-1.13-free", true, false, true)
	if err != nil {
		t.Fatalf("Route() anonymous Jev error = %v", err)
	}
	if anonymousRoute.Protocol != wire.SystemOne {
		t.Errorf("anonymous route protocol = %q, want %q", anonymousRoute.Protocol, wire.SystemOne)
	}
	if !anonymousRoute.Anonymous {
		t.Error("jev-1.13-free should use the anonymous Zen route when enabled")
	}

	keyRoute, err := catalog.Route("jev-1.13-free", true, false, false)
	if err != nil {
		t.Fatalf("Route() keyed Jev error = %v", err)
	}
	if keyRoute.Protocol != wire.SystemOne {
		t.Errorf("keyed route protocol = %q, want %q", keyRoute.Protocol, wire.SystemOne)
	}
}
