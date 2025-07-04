package telegram

import "testing"

func TestGetVersion(t *testing.T) {
	api, close, err := NewTelegramService(t.Context(), "123456", "your_api_hash_here")
	if err != nil {
		t.Fatalf("Failed to create TelegramService: %s", err)
	}
	defer close()
	_ = api

	/*
		optionValue, err := s.tdlibClient.GetOption(&client.GetOptionRequest{
			Name: "version",
		})
		if err != nil {
			log.Fatalf("GetOption error: %s", err)
		}

		log.Printf("TDLib version: %s", optionValue.(*client.OptionValueString).Value)
	*/
}

func (s *TelegramService) GetMe() {
	/*
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
	*/
}
