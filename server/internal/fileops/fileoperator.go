package fileops

import "io"

type LocalFileOperator interface {
	Move(src, dst string) error
	Copy(src, dst string) error
	Recycle(path string) error
	Rename(oldPath, newPath string) error
	Upload(dst string, content io.Reader) error
}
