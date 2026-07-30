package main

import (
	"context"
	"fmt"

	"example.com/bbk/api"
)

type stdoutStore struct{}

func (stdoutStore) Save(_ context.Context, record api.Record) error {
	fmt.Println(record.ID)
	return nil
}

func main() {
	service := api.NewService(stdoutStore{})
	_ = service.Save(context.Background(), api.Record{ID: "fixture"})
}
