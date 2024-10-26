package main

import (
	"log"
	"log/slog"
	"os"
	"os/signal"
	"syscall"
	"time"

	"teledeck/internal/config"
	external "teledeck/internal/service/external/api"

	tdlib "github.com/zelenin/go-tdlib/client"

	"github.com/joho/godotenv"
)

func main() {
	logger := slog.Default()
	err := godotenv.Load("../.env")
	if err != nil {
		log.Fatalf("godotenv.Load error: %s", err.Error())
	}

	cfg := config.MustLoadConfig()

	if err != nil {
		log.Fatalf("strconv.Atoi error: %s", err.Error())
	}

	slog.Info("cfg: ", "API ID", cfg.Telegram_API_ID, "API Hash", cfg.Telegram_API_Hash)

	tdService, err := external.NewTelegramService(cfg.Telegram_API_ID, cfg.Telegram_API_Hash, logger)

	if err != nil {
		logger.Error("NewTelegramService", "error", err.Error())
		return
	}

	// TODO: This should be a test library inside of telegramservice
	client := tdService.GetClient()
	listener := client.GetListener()
	defer listener.Close()

	go func() {
		for update := range listener.Updates {
			log.Printf("%#v", update)
			if update.GetType() == tdlib.TypeUpdateChatFolders {
				log.Printf("~~~*****************~~~")
				log.Printf("Chat folders: %#v", update)
				log.Printf("~~~*****************~~~")
			}
		}
	}()

	version, err := tdService.GetVersion()
	if err != nil {
		log.Fatalf("GetVersion error: %s", err)
	}

	log.Printf("TDLib version: %s", version)

	me, err := tdService.GetMe()
	if err != nil {
		log.Fatalf("GetMe error: %s", err)
	}

	logger.Info("GetMe", "FirstName", me)

	killSig := make(chan os.Signal, 2)
	signal.Notify(killSig, os.Interrupt, syscall.SIGTERM)

	time.Sleep(2 * time.Second)

	/*
		logger.Info("Loading chats...")
		client.LoadChats(
			&tdlib.LoadChatsRequest{
				ChatList: &tdlib.ChatListFolder{
					ChatFolderId: 1,
				},
				Limit: 10,
			})

		client.SetDatabaseEncryptionKey(&tdlib.SetDatabaseEncryptionKeyRequest{
			NewEncryptionKey: []byte{0x0, 0x0, 0x0},
		})
	*/

	<-killSig

	logger.Info("Bye now!")
	os.Exit(1)
}
