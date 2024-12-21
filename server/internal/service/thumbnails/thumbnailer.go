package thumbnails

import (
	"bytes"
	"fmt"
	"os"
	"os/exec"
	"path"
	"path/filepath"
)

type Thumbnailer struct {
	baseDir string
}

func NewThumbnailer(basedir string) *Thumbnailer {
	return &Thumbnailer{
		baseDir: basedir,
	}
}

func (t *Thumbnailer) GenerateVideoThumbnail(srcfile, outfile string) (outpath string, err error) {
	stats, err := os.Stat(srcfile)
	if err != nil {
		return "", fmt.Errorf("could not stat file: %w", err)
	}

	if stats.IsDir() {
		return "", fmt.Errorf("source is a directory")
	}

	if outfile == "" {
		outfile = filepath.Base(srcfile) + ".jpg"
	}

	outpath = path.Join(t.baseDir, outfile)

	/* Call ffmpeg on srcfile and save to outfile*/
	// How to tell if the command failed?
	// Note: check length of video first
	var outBuf, errBuf bytes.Buffer
	cmd := exec.Command("ffmpeg", "-i", srcfile, "-ss", "00:00:01.000", "-vframes", "1", outpath)
	cmd.Stdout = &outBuf
	cmd.Stderr = &errBuf
	err = cmd.Run()
	if err != nil {
		return "", fmt.Errorf("could not generate thumbnail: %w", cmd.Err)
	}
	fmt.Printf("ffmpeg output: %s\n", outBuf.String())
	fmt.Printf("ffmpeg error output: %s\n", errBuf.String())

	return outpath, nil
}
