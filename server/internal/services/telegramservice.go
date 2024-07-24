package services

import (
	"log"
	"path/filepath"
	"strconv"

	"github.com/zelenin/go-tdlib/client"
)

type TelegramService struct {
	tdlibClient *client.Client
}

func NewTelegramService(apiIdRaw, apiHash string) (*TelegramService, error) {

	apiId64, err := strconv.ParseInt(apiIdRaw, 10, 32)
	if err != nil {
		log.Fatalf("strconv.Atoi error: %s", err)
		return nil, err
	}

	apiId := int32(apiId64)
	authorizer := client.ClientAuthorizer()
	go client.CliInteractor(authorizer)

	authorizer.TdlibParameters <- &client.SetTdlibParametersRequest{
		UseTestDc:           false,
		DatabaseDirectory:   filepath.Join(".tdlib", "database"),
		FilesDirectory:      filepath.Join(".tdlib", "files"),
		UseFileDatabase:     true,
		UseChatInfoDatabase: true,
		UseMessageDatabase:  true,
		UseSecretChats:      false,
		ApiId:               apiId,
		ApiHash:             apiHash,
		SystemLanguageCode:  "en",
		DeviceModel:         "Server",
		SystemVersion:       "1.0.0",
		ApplicationVersion:  "1.0.0",
	}

	_, err = client.SetLogVerbosityLevel(&client.SetLogVerbosityLevelRequest{
		NewVerbosityLevel: 1,
	})
	if err != nil {
		log.Fatalf("SetLogVerbosityLevel error: %s", err)
		return nil, err
	}

	tdlibClient, err := client.NewClient(authorizer)
	if err != nil {
		log.Fatalf("NewClient error: %s", err)
		return nil, err
	}

	return &TelegramService{tdlibClient: tdlibClient}, nil

}

func (s *TelegramService) GetVersion() {
	optionValue, err := s.tdlibClient.GetOption(&client.GetOptionRequest{
		Name: "version",
	})

	if err != nil {
		log.Fatalf("GetOption error: %s", err)
	}

	log.Printf("TDLib version: %s", optionValue.(*client.OptionValueString).Value)
}

func (s *TelegramService) GetMe() {
	// client authorizer
	me, err := s.tdlibClient.GetMe()
	if err != nil {
		log.Fatalf("GetMe error: %s", err)
	}

	if me.Usernames != nil {
		log.Printf("Me: %s %s [%s]", me.FirstName, me.LastName, me.Usernames.ActiveUsernames)
	} else {
		log.Printf("Me: %s %s (No username)", me.FirstName, me.LastName)
	}

}

func (s *TelegramService) listenForUpdates() {

	listener := s.tdlibClient.GetListener()
	defer listener.Close()

	for update := range listener.Updates {
		if update.GetClass() == client.ClassUpdate {
			log.Printf("%#v", update)
		}
	}
}
