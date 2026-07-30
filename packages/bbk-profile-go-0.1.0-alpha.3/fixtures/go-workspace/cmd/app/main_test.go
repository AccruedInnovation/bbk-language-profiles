package main

import "testing"

func TestFixture(t *testing.T) {
	if got := 2 + 2; got != 4 {
		t.Fatalf("2+2 = %d", got)
	}
}
