package main

import (
	"encoding/json"
	"net/http"
	"os"
	"path/filepath"
)

var Port = "6969" // Default port, can be changed at build time using -ldflags "-X main.Port=XXXX"

type HealthResponse struct {
	Status  string `json:"status"`
	Message string `json:"message"`
	Port    string `json:"port"`
}

func main() {
	// API routes
	http.HandleFunc("/api/health", func(w http.ResponseWriter, r *http.Request) {
		response := HealthResponse{
			Status:  "OK",
			Message: "Service is running",
			Port:    Port,
		}
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(response)
	})

	// Serve React
	http.HandleFunc("/", spaHandler)

	http.ListenAndServe(":"+Port, nil)
}

// Default SPA handler to serve React app
func spaHandler(w http.ResponseWriter, r *http.Request) {
	path := filepath.Join("frontend/dist", r.URL.Path)

	if _, err := os.Stat(path); err == nil {
		http.ServeFile(w, r, path)
		return
	}
	http.ServeFile(w, r, filepath.Join("frontend/dist", "index.html"))
}
