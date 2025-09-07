package main

import (
	"fmt"
	"net/http"
)

func main() {
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		fmt.Fprintf(w, "Hello, I've seent it using GOlang at: %s\n", r.URL.Path)
	})

	http.ListenAndServe(":6969", nil)
}
