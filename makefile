# Makefile - build commands for amd64 windows and linux
BINARY ?= UnitedApp
OUTDIR ?= bin
LDFLAGS ?=

.PHONY: all build-windows build-linux clean

all-windows: build-linux-from-windows build-windows-from-windows
all-linux: build-linux-from-linux build-windows-from-linux

$(OUTDIR):
	mkdir -p $(OUTDIR)

build-windows-from-windows: $(OUTDIR)
	cmd /c "set GOOS=windows&&set GOARCH=amd64&&go build -o $(OUTDIR)/$(BINARY)_windows_amd64.exe HelloWorld.go $(LDFLAGS)"

build-linux-from-windows: $(OUTDIR)
	cmd /c "set GOOS=linux&&set GOARCH=amd64&&go build -o $(OUTDIR)/$(BINARY)_linux_amd64 HelloWorld.go $(LDFLAGS)"

build-windows-from-linux: $(OUTDIR)
	GOOS=windows GOARCH=amd64 go build -o $(OUTDIR)/$(BINARY)_windows_amd64.exe HelloWorld.go $(LDFLAGS)

build-linux-from-linux: $(OUTDIR)
	GOOS=linux GOARCH=amd64 go build -o $(OUTDIR)/$(BINARY)_linux_amd64 HelloWorld.go $(LDFLAGS)

clean:
	rm -rf $(OUTDIR)