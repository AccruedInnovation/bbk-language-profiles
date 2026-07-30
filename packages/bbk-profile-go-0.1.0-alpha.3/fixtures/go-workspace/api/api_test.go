package api

import (
	"context"
	"errors"
	"testing"
)

type memoryStore struct{ records []Record }

func (m *memoryStore) Save(_ context.Context, record Record) error {
	m.records = append(m.records, record)
	return nil
}

func TestServiceClose(t *testing.T) {
	store := &memoryStore{}
	service := NewService(store)
	service.Close()
	if err := service.Save(context.Background(), Record{ID: "x"}); !errors.Is(err, ErrClosed) {
		t.Fatalf("Save() error = %v, want ErrClosed", err)
	}
}

func FuzzRecordID(f *testing.F) {
	f.Add("seed")
	f.Fuzz(func(t *testing.T, value string) {
		if (Record{ID: value}).ID != value {
			t.Fatal("record ID changed")
		}
	})
}

func BenchmarkRecordCopy(b *testing.B) {
	record := Record{ID: "x", Value: make([]byte, 32)}
	for i := 0; i < b.N; i++ {
		_ = record
	}
}
