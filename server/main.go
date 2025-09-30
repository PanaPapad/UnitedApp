package main

import (
	"UnitedApp/internal/graphdb"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
)

var Port = "6969" // Default port, can be changed at build time using -ldflags "-X main.Port=XXXX"

type HealthResponse struct {
	DBStatus string `json:"db_status,omitempty"`
	Status   string `json:"status"`
	Message  string `json:"message"`
	Port     string `json:"port"`
}

func main() {
	// Create GraphDB client
	client, err := graphdb.NewClient()
	if err != nil {
		log.Fatalf("Failed to create GraphDB client: %v", err)
	}
	// API routes only
	http.HandleFunc("/api/health", func(w http.ResponseWriter, r *http.Request) {
		_, err := client.HealthCheck()
		var DBStatus string
		if err != nil {
			DBStatus = "DOWN"
		} else {
			DBStatus = "UP"
		}
		response := HealthResponse{
			DBStatus: DBStatus,
			Status:   "OK",
			Message:  "United App API is running",
			Port:     Port,
		}
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(response)
	})

	fmt.Printf("United App API running on port %s\n", Port)
	http.ListenAndServe(":"+Port, nil)
}
