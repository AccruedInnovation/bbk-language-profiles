package api

import (
	"context"
	"errors"
	"sync"
)

// ErrClosed is returned when the service has been closed.
var ErrClosed = errors.New("service closed")

// Record is the public wire representation used by the fixture.
type Record struct {
	ID    string            `json:"id"`
	Tags  map[string]string `json:"tags,omitempty"`
	Value []byte            `json:"value,omitempty"`
}

// Store is intentionally consumer-facing in this fixture.
type Store interface {
	Save(context.Context, Record) error
}

// Service owns a bounded worker lifecycle.
type Service struct {
	mu     sync.RWMutex
	closed bool
	store  Store
}

func NewService(store Store) *Service { return &Service{store: store} }

func (s *Service) Save(ctx context.Context, record Record) error {
	s.mu.RLock()
	closed := s.closed
	s.mu.RUnlock()
	if closed {
		return ErrClosed
	}
	if err := ctx.Err(); err != nil {
		return err
	}
	return s.store.Save(ctx, record)
}

func (s *Service) Close() {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.closed = true
}

// Stream copies records until input closes or the context is cancelled.
func Stream(ctx context.Context, input <-chan Record) <-chan Record {
	output := make(chan Record)
	go func() {
		defer close(output)
		for {
			select {
			case <-ctx.Done():
				return
			case record, ok := <-input:
				if !ok {
					return
				}
				select {
				case output <- record:
				case <-ctx.Done():
					return
				}
			}
		}
	}()
	return output
}
