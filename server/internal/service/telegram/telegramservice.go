// Package telegram provides methods to access the go-tdlib client
package telegram

import (
	"context"
	"log"

	// "path/filepath"
	"strconv"

	"github.com/gotd/td/telegram"
	"github.com/gotd/td/tg"
)

type TelegramService struct {
	client *tg.Client
}

func NewTelegramService(ctx context.Context, apiIDRaw, apiHash string) (svc TelegramService, close func(), err error) {
	apiID64, err := strconv.ParseInt(apiIDRaw, 10, 32)
	if err != nil {
		log.Fatalf("strconv.Atoi error: %s", err)
		return svc, close, err
	}

	apiID := int(apiID64)
	client := telegram.NewClient(apiID, apiHash, telegram.Options{})

	closeCtx, close := context.WithCancel(ctx)
	var api *tg.Client

	err = client.Run(closeCtx, func(tgCtx context.Context) error {
		api = client.API()

		<-tgCtx.Done()
		log.Println("Closing telegram client.")
		return nil
	})
	if err != nil {
		return svc, close, err
	}

	/*
		authorizer.TdlibParameters <- &client.SetTdlibParametersRequest{
			UseTestDc:           false,
			DatabaseDirectory:   filepath.Join(".tdlib", "database"),
			FilesDirectory:      filepath.Join(".tdlib", "files"),
			UseFileDatabase:     true,
			UseChatInfoDatabase: true,
			UseMessageDatabase:  true,
			UseSecretChats:      false,
			ApiId:               apiID,
			ApiHash:             apiHash,
			SystemLanguageCode:  "en",
			DeviceModel:         "Server",
			SystemVersion:       "1.0.0",
			ApplicationVersion:  "1.0.0",
		}
	*/

	return TelegramService{client: api}, close, nil
}

/*
func (s *TelegramService) ListenForUpdates() {
		listener := s.tdlibClient.GetListener()
		defer listener.Close()

		for update := range listener.Updates {
			if update.GetClass() == client.ClassUpdate {
				log.Printf("%#v", update)
			}
		}
}
*/
