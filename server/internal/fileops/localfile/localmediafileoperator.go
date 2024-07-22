package localfile

import (
	"io"
	"log/slog"
	"os"
	"path/filepath"
)

type LocalMediaFileOperator struct {
	baseDir    string
	recycleDir string
	logger     *slog.Logger
}

func NewLocalMediaFileOperator(baseDir, recycleDir string, logger *slog.Logger) *LocalMediaFileOperator {

	workDir, _ := os.Getwd()
	baseDir = filepath.Join(workDir, baseDir, "media")
	recycleDir = filepath.Join(workDir, recycleDir, "media")

	return &LocalMediaFileOperator{
		baseDir:    baseDir,
		recycleDir: recycleDir,
		logger:     logger,
	}
}

func (l *LocalMediaFileOperator) Move(src, dst string) error {
	return os.Rename(filepath.Join(l.baseDir, src), filepath.Join(l.baseDir, dst))
}

func (l *LocalMediaFileOperator) Copy(src, dst string) error {
	sourceFile, err := os.Open(filepath.Join(l.baseDir, src))
	if err != nil {
		return err
	}
	defer sourceFile.Close()

	destFile, err := os.Create(filepath.Join(l.baseDir, dst))
	if err != nil {
		return err
	}
	defer destFile.Close()

	_, err = io.Copy(destFile, sourceFile)
	return err
}

func (l *LocalMediaFileOperator) Recycle(path string) error {
	srcPath := filepath.Join(l.baseDir, path)
	dstPath := filepath.Join(l.recycleDir, path)

	if err := os.MkdirAll(filepath.Dir(dstPath), 0755); err != nil {
		return err
	}
	return os.Rename(srcPath, dstPath)
}

func (l *LocalMediaFileOperator) Rename(oldPath, newPath string) error {
	return os.Rename(filepath.Join(l.baseDir, oldPath), filepath.Join(l.baseDir, newPath))
}

func (l *LocalMediaFileOperator) Upload(dst string, content io.Reader) error {
	dstPath := filepath.Join(l.baseDir, dst)
	if err := os.MkdirAll(filepath.Dir(dstPath), 0755); err != nil {
		return err
	}

	file, err := os.Create(dstPath)
	if err != nil {
		return err
	}
	defer file.Close()

	_, err = io.Copy(file, content)
	return err
}
