package main

import (
	"encoding/json"
	"fmt"
	"net/http"
)

var Port = "6969" // Default port, can be changed at build time using -ldflags "-X main.Port=XXXX"

type HealthResponse struct {
	Status  string `json:"status"`
	Message string `json:"message"`
	Port    string `json:"port"`
}

func main() {
	// API routes only
	http.HandleFunc("/api/health", func(w http.ResponseWriter, r *http.Request) {
		response := HealthResponse{
			Status:  "OK",
			Message: "United App API is running",
			Port:    Port,
		}
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(response)
	})

	fmt.Printf("United App API running on port %s\n", Port)
	http.ListenAndServe(":"+Port, nil)
}
