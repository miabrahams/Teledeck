package thumbnailer

import (
	"path"
	"path/filepath"
	"testing"

	"github.com/stretchr/testify/require"
)

func TestThumbnailer_GenerateVideoThumbnail(t *testing.T) {
	/*
		type fields struct {
			baseDir string
		}
		type args struct {
			srcfile string
			outfile string
		}
		tests := []struct {
			name    string
			fields  fields
			args    args
			want    string
			wantErr bool
		}
	*/

	staticRoot, err := filepath.Abs("../../../../static")
	require.NoError(t, err)

	thumbRoot := path.Join(staticRoot, "thumbnails")
	mediaRoot := path.Join(staticRoot, "media")
	testVid := path.Join(mediaRoot, "1.mp4")

	thumbnailer := NewThumbnailer(thumbRoot, 1)

	out, err := thumbnailer.generateVideoThumbnail(testVid, "")
	require.NoError(t, err)

	require.Equal(t, path.Join(thumbRoot, "1.mp4.jpg"), out)
	require.FileExists(t, out)

}
