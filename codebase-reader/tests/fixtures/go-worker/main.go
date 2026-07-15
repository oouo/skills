package main

import (
	"context"
	"errors"
	"fmt"
	"os"
	"os/signal"
	"sync"
)

type Job struct {
	ID string
}

func process(ctx context.Context, job Job) error {
	select {
	case <-ctx.Done():
		return ctx.Err()
	default:
	}
	if job.ID == "" {
		return errors.New("missing job ID")
	}
	fmt.Println(job.ID)
	return nil
}

func run(ctx context.Context, jobs <-chan Job) error {
	var workers sync.WaitGroup
	errorsOut := make(chan error, 1)
	workers.Add(1)
	go func() {
		defer workers.Done()
		for job := range jobs {
			if err := process(ctx, job); err != nil {
				errorsOut <- err
				return
			}
		}
	}()

	done := make(chan struct{})
	go func() {
		defer close(done)
		workers.Wait()
	}()

	select {
	case <-ctx.Done():
		return ctx.Err()
	case err := <-errorsOut:
		return err
	case <-done:
		return nil
	}
}

func main() {
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt)
	defer stop()
	jobs := make(chan Job, 1)
	jobs <- Job{ID: "fixture"}
	close(jobs)
	if err := run(ctx, jobs); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
