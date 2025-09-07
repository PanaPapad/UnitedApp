package main

import (
	"fmt"
	"net/http"
)

var Port = "6969" // Default port, can be changed at build time using -ldflags "-X main.Port=XXXX"

func main() {
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		fmt.Fprintf(w, "Hello, I've seent it using GO at: %s\n", r.URL.Path)
	})

	http.ListenAndServe(":"+Port, nil)
}
