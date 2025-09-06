package thumbnailer

import (
	"bytes"
	"errors"
	"fmt"
	"log/slog"
	"os"
	"os/exec"
	"path"
	"path/filepath"
	"strings"
	"sync"
)

type Thumbnailer struct {
	baseDir       string
	inFlightMap   map[string]struct{}
	inFlightMutex sync.Mutex
	queue         chan item
	results       chan Result
	workerCount   int
	callback      func(Result)
}

type item struct {
	srcfile       string
	outfile       string
	correlationID any
}

type Result struct {
	Srcfile       string
	Outpath       string
	CorrelationID any
	Err           error
}

var (
	ErrThumbnailInProgress = errors.New("thumbnail generation in progress")
	ErrQueueFull           = errors.New("thumbnail queue full")
)

func NewThumbnailer(basedir string, workerCount int) *Thumbnailer {
	t := &Thumbnailer{
		baseDir:     basedir,
		workerCount: workerCount,
		inFlightMap: make(map[string]struct{}),
		queue:       make(chan item, 100),
		results:     make(chan Result, 100),
	}
	return t
}

func (t *Thumbnailer) BaseDir() string {
	return t.baseDir
}

func (t *Thumbnailer) SetHandler(cb func(Result)) {
	t.callback = cb
	for i := 0; i < t.workerCount; i++ {
		go t.worker()
	}
	go t.handleResults()
}

func (t *Thumbnailer) worker() {
	for input := range t.queue {
		outpath, err := t.generateVideoThumbnail(input.srcfile, input.outfile)
		slog.Info("Thumbnail generation complete", "srcfile", input.srcfile, "outpath", outpath, "err", err)
		t.results <- Result{CorrelationID: input.correlationID, Outpath: outpath, Err: err}
	}
}

func (t *Thumbnailer) handleResults() {
	for res := range t.results {
		t.inFlightMutex.Lock()
		delete(t.inFlightMap, res.Srcfile)
		t.inFlightMutex.Unlock()
		if t.callback != nil {
			t.callback(res)
		}
	}
}

func (t *Thumbnailer) generateVideoThumbnail(srcfile, outfile string) (outpath string, err error) {
	fmt.Println("1")
	stats, err := os.Stat(srcfile)
	if err != nil {
		return "", fmt.Errorf("could not stat file: %w", err)
	}
	fmt.Println("2")

	if stats.IsDir() {
		return "", fmt.Errorf("source is a directory")
	}
	fmt.Println("3")

	if outfile == "" {
		outfile = strings.ReplaceAll(filepath.Base(srcfile), filepath.Ext(srcfile), "")
		outfile = strings.ReplaceAll(outfile, " ", "_")
		// outfile = uuid.NewString()
		// slog.Info("Output file not specified, using generated name", "outfile", outfile)
		outfile += ".jpg"
	}

	outpath = path.Join(t.baseDir, outfile)

	/* Call ffmpeg on srcfile and save to outfile*/
	// How to tell if the command failed?
	// Note: may fail for short videos. Add test please!!
	fmt.Println("4")
	var outBuf, errBuf bytes.Buffer
	cmd := exec.Command("ffmpeg", "-i", srcfile, "-vf", "thumbnail", "-update", "true", "-frames:v", "1", outpath)
	fmt.Println("5")
	fmt.Println("Running ffmpeg: " + cmd.String())
	cmd.Stdout = &outBuf
	cmd.Stderr = &errBuf
	err = cmd.Run()
	if err != nil {
		fmt.Printf("ffmpeg output: \nstdout: %s\nstderr:%s", outBuf.String(), errBuf.String())
		return "", fmt.Errorf("could not generate thumbnail: %w", err)
	}

	return outfile, nil
}

// TODO: Some error checking??
func (t *Thumbnailer) GenerateVideoThumbnail(srcfile, outfile string, correlationID any) (err error) {
	slog.Info("Generating thumbnail for video", "srcfile", srcfile, "outfile", outfile)
	t.inFlightMutex.Lock()
	if _, ok := t.inFlightMap[srcfile]; ok {
		t.inFlightMutex.Unlock()
		return nil
	}
	t.inFlightMap[srcfile] = struct{}{}
	t.inFlightMutex.Unlock()

	t.queue <- item{srcfile: srcfile, outfile: outfile, correlationID: correlationID}
	return nil
}
