package hazards

import (
	"context"
	"fmt"
)

type Failure struct{}

func (*Failure) Error() string { return "failure" }

// TypedNil returns a non-nil interface containing a nil pointer.
func TypedNil() error {
	var failure *Failure
	return failure
}

// MapText exposes map iteration order in user-visible output.
func MapText(values map[string]int) string {
	result := ""
	for key, value := range values {
		result += fmt.Sprintf("%s=%d;", key, value)
	}
	return result
}

// Leak starts a goroutine with no owner, join, or cancellation behavior.
func Leak(_ context.Context) {
	go func() { select {} }()
}
