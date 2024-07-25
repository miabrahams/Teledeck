package models

func IsPhoto(typename string) bool {
	return typename == "photo" || typename == "image" || typename == "png" || typename == "jpeg" || typename == "webp"
}

func IsImgElement(typename string) bool {
	return IsPhoto(typename) || typename == "gif"
}

func IsVideoElement(typename string) bool {
	return typename == "video" || typename == "webm" || typename == "document" || typename == "mp4"
}
