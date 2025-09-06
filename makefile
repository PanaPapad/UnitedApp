# Makefile - build commands for amd64 windows and linux
BINARY ?= UnitedApp
OUTDIR ?= bin
LDFLAGS ?=

.PHONY: all build-windows build-linux clean

all: build-linux build-windows

$(OUTDIR):
	mkdir -p $(OUTDIR)

build-windows: $(OUTDIR)
	cmd /c "set GOOS=windows&&set GOARCH=amd64&&go build -o $(OUTDIR)/$(BINARY)_windows_amd64.exe HelloWorld.go"

build-linux: $(OUTDIR)
	cmd /c "set GOOS=linux&&set GOARCH=amd64&&go build -o $(OUTDIR)/$(BINARY)_linux_amd64 HelloWorld.go"

clean:
	rm -rf $(OUTDIR)