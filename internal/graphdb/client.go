package graphdb

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"

	"github.com/joho/godotenv"
)

type Client struct {
	URL        string
	Username   string
	Password   string
	httpClient *http.Client
}

func NewClient() (*Client, error) {
	err := godotenv.Load()
	if err != nil {
		return nil, fmt.Errorf("error loading .env file: %w", err)
	}

	host := os.Getenv("GRAPHDB_HOST")
	repo := os.Getenv("GRAPHDB_REPOSITORY")

	return &Client{
		URL:        fmt.Sprintf("https://%s/repositories/%s", host, repo),
		Username:   os.Getenv("GRAPHDB_USERNAME"),
		Password:   os.Getenv("GRAPHDB_PASSWORD"),
		httpClient: &http.Client{},
	}, nil
}

func (c *Client) HealthCheck() (map[string]interface{}, error) {
	var healthCheckUrl = c.URL + "/health"
	req, err := http.NewRequest("GET", healthCheckUrl, nil)
	if err != nil {
		return nil, err
	}
	req.Header.Set("Accept", "application/json")
	if c.Username != "" && c.Password != "" {
		req.SetBasicAuth(c.Username, c.Password)
	}

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("error: %s", body)
	}

	var result map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}

	return result, nil
}
