# Recursos REST da LCU (via eventos do /help) — total 924
# (cada recurso normalmente aceita GET; muitos aceitam POST/PUT/DELETE)


## chat  (7)
  /chat/v1/session
  /chat/v1/settings
  /chat/v3/errors
  /chat/v3/groups
  /chat/v5/messages
  /chat/v5/participants
  /chat/v6/conversations

## client-config  (3)
  /client-config/v1/status
  /client-config/v2/config
  /client-config/v2/namespace

## data-store  (2)
  /data-store/v1/install-settings
  /data-store/v1/system-settings

## deep-links  (1)
  /deep-links/v1/settings

## entitlements  (3)
  /entitlements/v1/entitlements
  /entitlements/v1/token
  /entitlements/v2/token

## error-monitor  (1)
  /error-monitor/v1/logs

## ga-restriction  (1)
  /ga-restriction/v1/penalty-notifications

## lol-account-verification  (1)
  /lol-account-verification/v1/is-verified

## lol-active-boosts  (1)
  /lol-active-boosts/v1/active-boosts

## lol-activity-center  (1)
  /lol-activity-center/v1/ready

## lol-anti-addiction  (1)
  /lol-anti-addiction/v1/anti-addiction-token

## lol-cap-missions  (1)
  /lol-cap-missions/v1/ready

## lol-catalog  (2)
  /lol-catalog/v1/items
  /lol-catalog/v1/ready

## lol-challenges  (7)   <== relevante
  /lol-challenges/v1/challenges
  /lol-challenges/v1/client-state
  /lol-challenges/v1/my-updated-challenges
  /lol-challenges/v1/penalty
  /lol-challenges/v1/seasons
  /lol-challenges/v1/summary-player-data
  /lol-challenges/v1/updated-challenges

## lol-champ-select  (16)   <== relevante
  /lol-champ-select/v1/all-grid-champions
  /lol-champ-select/v1/aw-set
  /lol-champ-select/v1/bannable-champion-ids
  /lol-champ-select/v1/current-champion
  /lol-champ-select/v1/disabled-champion-ids
  /lol-champ-select/v1/grid-champions
  /lol-champ-select/v1/muted-players
  /lol-champ-select/v1/ongoing-champion-swap
  /lol-champ-select/v1/pickable-champion-ids
  /lol-champ-select/v1/pin-drop-notification
  /lol-champ-select/v1/session
  /lol-champ-select/v1/sfx-notifications
  /lol-champ-select/v1/skin-carousel-skins
  /lol-champ-select/v1/skin-selector-info
  /lol-champ-select/v1/summoners
  /lol-champ-select/v1/team-boost

## lol-champ-select-legacy  (8)
  /lol-champ-select-legacy/v1/bannable-champion-ids
  /lol-champ-select-legacy/v1/current-champion
  /lol-champ-select-legacy/v1/disabled-champion-ids
  /lol-champ-select-legacy/v1/implementation-active
  /lol-champ-select-legacy/v1/pickable-champion-ids
  /lol-champ-select-legacy/v1/pickable-skin-ids
  /lol-champ-select-legacy/v1/session
  /lol-champ-select-legacy/v1/team-boost

## lol-champion-mastery  (4)
  /lol-champion-mastery/v1/champion-mastery-view
  /lol-champion-mastery/v1/local-player
  /lol-champion-mastery/v1/notifications
  /lol-champion-mastery/v1/ready

## lol-champions  (2)
  /lol-champions/v1/inventories
  /lol-champions/v1/owned-champions-minimal

## lol-chat  (15)   <== relevante
  /lol-chat/v1/blocked-players
  /lol-chat/v1/config
  /lol-chat/v1/conversations
  /lol-chat/v1/discord-link-status
  /lol-chat/v1/friend-counts
  /lol-chat/v1/friend-groups
  /lol-chat/v1/friend-requests
  /lol-chat/v1/friends
  /lol-chat/v1/is-discord-integration-enabled
  /lol-chat/v1/is-discord-linked
  /lol-chat/v1/me
  /lol-chat/v1/player-mutes
  /lol-chat/v1/resources
  /lol-chat/v1/session
  /lol-chat/v1/settings

## lol-clash  (20)
  /lol-clash/v1/all-tournaments
  /lol-clash/v1/bracket
  /lol-clash/v1/checkin-allowed
  /lol-clash/v1/currentTournamentIds
  /lol-clash/v1/disabled-config
  /lol-clash/v1/enabled
  /lol-clash/v1/iconconfig
  /lol-clash/v1/invited-roster-ids
  /lol-clash/v1/player
  /lol-clash/v1/playmode-restricted
  /lol-clash/v1/ready
  /lol-clash/v1/roster
  /lol-clash/v1/simple-state-flags
  /lol-clash/v1/time
  /lol-clash/v1/tournament
  /lol-clash/v1/tournament-state-info
  /lol-clash/v1/tournament-summary
  /lol-clash/v1/visible
  /lol-clash/v1/voice-enabled
  /lol-clash/v2/playmode-restricted

## lol-client-config  (1)
  /lol-client-config/v3/client-config

## lol-collections  (1)   <== relevante
  /lol-collections/v1/inventories

## lol-cosmetics  (2)   <== relevante
  /lol-cosmetics/v1/favorites
  /lol-cosmetics/v1/inventories

## lol-directx-upgrade  (1)
  /lol-directx-upgrade/needs-hardware-upgrade

## lol-drops  (1)
  /lol-drops/v1/ready

## lol-end-of-game  (4)   <== relevante
  /lol-end-of-game/v1/champion-mastery-updates
  /lol-end-of-game/v1/eog-stats-block
  /lol-end-of-game/v1/gameclient-eog-stats-block
  /lol-end-of-game/v1/tft-eog-stats

## lol-event-hub  (4)
  /lol-event-hub/v1/events
  /lol-event-hub/v1/navigation-button-data
  /lol-event-hub/v1/skins
  /lol-event-hub/v1/token-upsell

## lol-event-mission  (1)
  /lol-event-mission/v1/event-mission

## lol-game-client-chat  (6)
  /lol-game-client-chat/v1/buddies
  /lol-game-client-chat/v1/instant-messages
  /lol-game-client-chat/v2/buddies
  /lol-game-client-chat/v2/instant-messages
  /lol-game-client-chat/v2/parental-controls-status
  /lol-game-client-chat/v2/playtime-reminder-hours-played

## lol-game-data-inventory  (1)
  /lol-game-data-inventory/v1/ready

## lol-game-queues  (4)
  /lol-game-queues/v1/custom
  /lol-game-queues/v1/custom-non-default
  /lol-game-queues/v1/matchmaking-queues
  /lol-game-queues/v1/queues

## lol-game-settings  (3)
  /lol-game-settings/v1/game-settings
  /lol-game-settings/v1/input-settings
  /lol-game-settings/v1/ready

## lol-gameflow  (9)   <== relevante
  /lol-gameflow/v1/active-patcher-lock
  /lol-gameflow/v1/availability
  /lol-gameflow/v1/battle-training
  /lol-gameflow/v1/early-exit-notifications
  /lol-gameflow/v1/gameflow-metadata
  /lol-gameflow/v1/gameflow-phase
  /lol-gameflow/v1/session
  /lol-gameflow/v1/spectate
  /lol-gameflow/v1/watch

## lol-highlights  (2)
  /lol-highlights/v1/config
  /lol-highlights/v1/highlights-folder-path

## lol-honeyfruit  (1)
  /lol-honeyfruit/v1/vng-publisher-settings

## lol-honor-v2  (12)   <== relevante
  /lol-honor-v2/v1/ballot
  /lol-honor-v2/v1/config
  /lol-honor-v2/v1/late-recognition
  /lol-honor-v2/v1/latest-eligible-game
  /lol-honor-v2/v1/level-change
  /lol-honor-v2/v1/mutual-honor
  /lol-honor-v2/v1/profile
  /lol-honor-v2/v1/recipients
  /lol-honor-v2/v1/recognition
  /lol-honor-v2/v1/recognition-history
  /lol-honor-v2/v1/team-choices
  /lol-honor-v2/v1/vote-completion

## lol-hovercard  (1)
  /lol-hovercard/v1/friend-info

## lol-inventory  (6)
  /lol-inventory/v1/initial-configuration-complete
  /lol-inventory/v1/inventory
  /lol-inventory/v1/notifications
  /lol-inventory/v1/signedInventory
  /lol-inventory/v1/wallet
  /lol-inventory/v2/inventory

## lol-kr-playtime-reminder  (1)
  /lol-kr-playtime-reminder/v1/hours-played

## lol-leaderboard  (1)
  /lol-leaderboard/v1/ready

## lol-league-session  (1)
  /lol-league-session/v1/league-session-token

## lol-leaver-buster  (1)
  /lol-leaver-buster/v1/ranked-restriction

## lol-loadouts  (4)
  /lol-loadouts/v1/enabled
  /lol-loadouts/v1/loadouts-ready
  /lol-loadouts/v4/loadout
  /lol-loadouts/v4/loadouts

## lol-lobby  (9)   <== relevante
  /lol-lobby/v1/last-queued-lobby
  /lol-lobby/v1/lobby
  /lol-lobby/v1/party-rewards
  /lol-lobby/v2/comms
  /lol-lobby/v2/eligibility
  /lol-lobby/v2/lobby
  /lol-lobby/v2/party
  /lol-lobby/v2/party-active
  /lol-lobby/v2/received-invitations

## lol-lobby-team-builder  (2)
  /lol-lobby-team-builder/champ-select/v1
  /lol-lobby-team-builder/v1/matchmaking

## lol-lock-and-load  (3)
  /lol-lock-and-load/v1/home-hubs-waits
  /lol-lock-and-load/v1/should-show-progress-bar-text
  /lol-lock-and-load/v1/should-wait-for-home-hubs

## lol-login  (6)
  /lol-login/v1/login-connection-state
  /lol-login/v1/login-data-packet
  /lol-login/v1/login-in-game-creds
  /lol-login/v1/login-platform-credentials
  /lol-login/v1/session
  /lol-login/v2/league-session-init-token

## lol-loot  (6)   <== relevante
  /lol-loot/v1/currency-configuration
  /lol-loot/v1/enabled
  /lol-loot/v1/loot-grants
  /lol-loot/v1/milestones
  /lol-loot/v1/ready
  /lol-loot/v1/recipes

## lol-loyalty  (1)
  /lol-loyalty/v1/status-notification

## lol-mac-graphics-upgrade  (1)
  /lol-mac-graphics-upgrade/needs-hardware-upgrade

## lol-maps  (2)
  /lol-maps/v1/maps
  /lol-maps/v2/maps

## lol-marketing-preferences  (1)
  /lol-marketing-preferences/v1/ready

## lol-marketplace  (2)
  /lol-marketplace/v1/products
  /lol-marketplace/v1/ready

## lol-matchmaking  (2)   <== relevante
  /lol-matchmaking/v1/ready-check
  /lol-matchmaking/v1/search

## lol-metagames  (1)
  /lol-metagames/v1/ready

## lol-missions  (2)
  /lol-missions/v1/missions
  /lol-missions/v1/series

## lol-npe-tutorial-path  (3)
  /lol-npe-tutorial-path/v1/rewards
  /lol-npe-tutorial-path/v1/settings
  /lol-npe-tutorial-path/v1/tutorials

## lol-objectives  (2)
  /lol-objectives/v1/objectives
  /lol-objectives/v1/ready

## lol-parental-controls  (1)
  /lol-parental-controls/v1/status

## lol-patch  (6)
  /lol-patch/v1/checking-enabled
  /lol-patch/v1/environment
  /lol-patch/v1/game-version
  /lol-patch/v1/notifications
  /lol-patch/v1/products
  /lol-patch/v1/status

## lol-perks  (7)   <== relevante
  /lol-perks/v1/currentpage
  /lol-perks/v1/inventory
  /lol-perks/v1/pages
  /lol-perks/v1/perks
  /lol-perks/v1/rune-recommender-auto-select
  /lol-perks/v1/settings
  /lol-perks/v1/styles

## lol-platform-config  (567)
  /lol-platform-config/v1/initial-configuration-complete
  /lol-platform-config/v1/namespace/Parties/PublishPresenceDelay
  /lol-platform-config/v1/namespaces
  /lol-platform-config/v1/namespaces/AccountVerification
  /lol-platform-config/v1/namespaces/AccountVerification/Enabled
  /lol-platform-config/v1/namespaces/AccountVerification/KrPhoneDisplayEnabled
  /lol-platform-config/v1/namespaces/AccountVerification/PasswordEnabled
  /lol-platform-config/v1/namespaces/AccountVerification/PhoneValidationEnabled
  /lol-platform-config/v1/namespaces/AccountVerification/SettingsEnabled
  /lol-platform-config/v1/namespaces/AccountVerification/SettingsVerifyEnabled
  /lol-platform-config/v1/namespaces/AccountVerification/TencentPhoneDisplayEnabled
  /lol-platform-config/v1/namespaces/Banners
  /lol-platform-config/v1/namespaces/Banners/IsEnabledOnProfile
  /lol-platform-config/v1/namespaces/Banners/IsEquipEnabled
  /lol-platform-config/v1/namespaces/Banners/IsOtherSummonersProfileEnabled
  /lol-platform-config/v1/namespaces/BotConfigurations
  /lol-platform-config/v1/namespaces/BotConfigurations/IntermediateInCustoms
  /lol-platform-config/v1/namespaces/BotConfigurations/RiotscriptInCustoms
  /lol-platform-config/v1/namespaces/CareerStats
  /lol-platform-config/v1/namespaces/CareerStats/StatsEnabled
  /lol-platform-config/v1/namespaces/Challenges
  /lol-platform-config/v1/namespaces/Challenges/ChallengeUpdateDelaySeconds
  /lol-platform-config/v1/namespaces/Challenges/ClientState
  /lol-platform-config/v1/namespaces/Challenges/CollectionEnabled
  /lol-platform-config/v1/namespaces/Challenges/DarkModeAllowlistOnly
  /lol-platform-config/v1/namespaces/Challenges/EnabledInventoryTypes
  /lol-platform-config/v1/namespaces/Challenges/FeatureIntroEnabled
  /lol-platform-config/v1/namespaces/Challenges/LobbyChallengesEnabled
  /lol-platform-config/v1/namespaces/Challenges/MaxNotificationSubscriptionDelaySeconds
  /lol-platform-config/v1/namespaces/Challenges/MaxWaitTimeBeforeNotificationSubscriptionSeconds
  /lol-platform-config/v1/namespaces/Challenges/NumberOfSuggestedChallenges
  /lol-platform-config/v1/namespaces/Challenges/SeasonalTooltipEnabled
  /lol-platform-config/v1/namespaces/Challenges/WaitTimeBeforeCallChallengeUpdateSeconds
  /lol-platform-config/v1/namespaces/Challenges/WaitTimeBeforeDarkModeAdditionalCallsSeconds
  /lol-platform-config/v1/namespaces/ChampionMasteryConfig
  /lol-platform-config/v1/namespaces/ChampionMasteryConfig/ChampionPointQueueTypes
  /lol-platform-config/v1/namespaces/ChampionMasteryConfig/Enabled
  /lol-platform-config/v1/namespaces/ChampionMasteryConfig/EndOfGameEnabled
  /lol-platform-config/v1/namespaces/ChampionMasteryConfig/MaxChampionLevel
  /lol-platform-config/v1/namespaces/ChampionMasteryConfig/MinSummonerLevel
  /lol-platform-config/v1/namespaces/ChampionMasteryConfig/SupportedQueueTypes
  /lol-platform-config/v1/namespaces/ChampionSelect
  /lol-platform-config/v1/namespaces/ChampionSelect/AllChampsAvailableInAram
  /lol-platform-config/v1/namespaces/ChampionSelect/AlwaysShowRewardIcon
  /lol-platform-config/v1/namespaces/ChampionSelect/AutoReconnectEnabled
  /lol-platform-config/v1/namespaces/ChampionSelect/CollatorChampionFilterEnabled
  /lol-platform-config/v1/namespaces/ChampionSelect/UseOptimizedBotChampionSelectProcessor
  /lol-platform-config/v1/namespaces/ChampionSelect/UseOptimizedChampSelectProcessor
  /lol-platform-config/v1/namespaces/ChampionSelect/UseOptimizedSpellSelectProcessor
  /lol-platform-config/v1/namespaces/Chat
  /lol-platform-config/v1/namespaces/Chat/MaximumRosterSize
  /lol-platform-config/v1/namespaces/ChatDomain
  /lol-platform-config/v1/namespaces/ChatDomain/ChampSelectDomainName
  /lol-platform-config/v1/namespaces/ChatDomain/PostGameDomainName
  /lol-platform-config/v1/namespaces/Chroma
  /lol-platform-config/v1/namespaces/Chroma/IsEnabled
  /lol-platform-config/v1/namespaces/Clash
  /lol-platform-config/v1/namespaces/Clash/AramIntroModalEnabled
  /lol-platform-config/v1/namespaces/ClashConfig
  /lol-platform-config/v1/namespaces/ClashConfig/AntiCheatModalEnabled
  /lol-platform-config/v1/namespaces/ClashConfig/AramIntroModalEnabled
  /lol-platform-config/v1/namespaces/ClashConfig/AwardsTabEnabled
  /lol-platform-config/v1/namespaces/ClashConfig/BracketSpectateEnabled
  /lol-platform-config/v1/namespaces/ClashConfig/CapacityIndicatorEnabled
  /lol-platform-config/v1/namespaces/ClashConfig/ClashStartModalEnabled
  /lol-platform-config/v1/namespaces/ClashConfig/EatTooltipEnabled
  /lol-platform-config/v1/namespaces/ClashConfig/EnabledState
  /lol-platform-config/v1/namespaces/ClashConfig/EndOfGameFlowEnabled
  /lol-platform-config/v1/namespaces/ClashConfig/FaqLinkOverride
  /lol-platform-config/v1/namespaces/ClashConfig/FindTeamViewEnabled
  /lol-platform-config/v1/namespaces/ClashConfig/HonorLevelRequired
  /lol-platform-config/v1/namespaces/ClashConfig/IconConfig
  /lol-platform-config/v1/namespaces/ClashConfig/InviteModalTiersEnabled
  /lol-platform-config/v1/namespaces/ClashConfig/IsRewardsModalEnabled
  /lol-platform-config/v1/namespaces/ClashConfig/LftEnabled
  /lol-platform-config/v1/namespaces/ClashConfig/LoginModalEnabled
  /lol-platform-config/v1/namespaces/ClashConfig/PremiumTicketsEnabled
  /lol-platform-config/v1/namespaces/ClashConfig/ScoutingEnabled
  /lol-platform-config/v1/namespaces/ClashConfig/StorePageLink
  /lol-platform-config/v1/namespaces/ClashConfig/ThirdPartyInvitesEnabled
  /lol-platform-config/v1/namespaces/ClashConfig/TutorialEnabled
  /lol-platform-config/v1/namespaces/ClashConfig/Visibility
  /lol-platform-config/v1/namespaces/ClientSystemStates
  /lol-platform-config/v1/namespaces/ClientSystemStates/knownGeographicGameServerRegions
  /lol-platform-config/v1/namespaces/Clubs
  /lol-platform-config/v1/namespaces/Clubs/ClubsEnabled
  /lol-platform-config/v1/namespaces/Companions
  /lol-platform-config/v1/namespaces/Companions/SelectorInChampSelectEnabled
  /lol-platform-config/v1/namespaces/ContextualEducation
  /lol-platform-config/v1/namespaces/ContextualEducation/Enabled
  /lol-platform-config/v1/namespaces/ContextualEducation/MaxTargetSummonerLevel
  /lol-platform-config/v1/namespaces/ContextualEducation/TargetMinionsPerWave
  /lol-platform-config/v1/namespaces/ContextualEducationURLs
  /lol-platform-config/v1/namespaces/ContextualEducationURLs/LAST/HIT
  /lol-platform-config/v1/namespaces/CustomGame
  /lol-platform-config/v1/namespaces/CustomGame/BotsAvailableInAram
  /lol-platform-config/v1/namespaces/CustomGame/MinorRestrictionsEnabled
  /lol-platform-config/v1/namespaces/DisabledChampionSkins
  /lol-platform-config/v1/namespaces/DisabledChampionSkins/DisabledChromas
  /lol-platform-config/v1/namespaces/DisabledChampionSkins/LegacyDisabledChampionSkins
  /lol-platform-config/v1/namespaces/DiscordRP
  /lol-platform-config/v1/namespaces/DiscordRP/IsEnabled
  /lol-platform-config/v1/namespaces/DockedPrompt
  /lol-platform-config/v1/namespaces/DockedPrompt/EnabledNewDockedPromptRenderer
  /lol-platform-config/v1/namespaces/Emotes
  /lol-platform-config/v1/namespaces/Emotes/IsEmotePanelEnabled
  /lol-platform-config/v1/namespaces/Esports
  /lol-platform-config/v1/namespaces/Esports/NotificationsAssetMagickURL
  /lol-platform-config/v1/namespaces/Esports/NotificationsEnabled
  /lol-platform-config/v1/namespaces/Esports/NotificationsServiceEndpoint
  /lol-platform-config/v1/namespaces/Esports/NotificationsStreamGroupSlug
  /lol-platform-config/v1/namespaces/Esports/NotificationsStreamURL
  /lol-platform-config/v1/namespaces/Eternals
  /lol-platform-config/v1/namespaces/Eternals/Enabled
  /lol-platform-config/v1/namespaces/Eternals/ServiceUrl
  /lol-platform-config/v1/namespaces/FeaturedGame
  /lol-platform-config/v1/namespaces/FeaturedGame/MetadataEnabled
  /lol-platform-config/v1/namespaces/FeaturedModes
  /lol-platform-config/v1/namespaces/FeaturedModes/DisabledRgmButtonEnabled
  /lol-platform-config/v1/namespaces/FeaturedModes/GoldenSpatulaClubDisabled
  /lol-platform-config/v1/namespaces/FeaturedModes/MaxNotificationSaveDelayMinutes
  /lol-platform-config/v1/namespaces/FeaturedModes/NotificationsEnabled
  /lol-platform-config/v1/namespaces/FeaturedModes/QueuesDelayedRefreshMaxTimeout
  /lol-platform-config/v1/namespaces/FeaturedModes/QueuesDelayedRefreshMinTimeout
  /lol-platform-config/v1/namespaces/GameInvites
  /lol-platform-config/v1/namespaces/GameInvites/InviteBulkMaxSize
  /lol-platform-config/v1/namespaces/GameInvites/LobbyCreationEnabled
  /lol-platform-config/v1/namespaces/GameInvites/ServiceEnabled
  /lol-platform-config/v1/namespaces/GameTimerSync
  /lol-platform-config/v1/namespaces/GameTimerSync/PercentOfTotalTimerToSyncAt
  /lol-platform-config/v1/namespaces/Gameflow/ShouldSendRiotClientHeartBeat
  /lol-platform-config/v1/namespaces/Highlights
  /lol-platform-config/v1/namespaces/Highlights/Enabled
  /lol-platform-config/v1/namespaces/Inventory
  /lol-platform-config/v1/namespaces/Inventory/BaseServiceUrl
  /lol-platform-config/v1/namespaces/Inventory/Enabled
  /lol-platform-config/v1/namespaces/ItemSets
  /lol-platform-config/v1/namespaces/ItemSets/EditorEnabled
  /lol-platform-config/v1/namespaces/ItemSets/MaxItemSets
  /lol-platform-config/v1/namespaces/ItemSets/RestrictedPageNamesEnabled
  /lol-platform-config/v1/namespaces/ItemSets/SendItemSetsToGame
  /lol-platform-config/v1/namespaces/Kickout
  /lol-platform-config/v1/namespaces/Kickout/Enabled
  /lol-platform-config/v1/namespaces/Kickout/SecurityCheckEnabled
  /lol-platform-config/v1/namespaces/Kickout/SecurityCheckUrl
  /lol-platform-config/v1/namespaces/KrPlaytimeReminder
  /lol-platform-config/v1/namespaces/KrPlaytimeReminder/Enabled
  /lol-platform-config/v1/namespaces/LCUCollections
  /lol-platform-config/v1/namespaces/LCUCollections/LCUCollectiblesChromasEnabled
  /lol-platform-config/v1/namespaces/LCUCollections/LCUCollectiblesFinishersEnabled
  /lol-platform-config/v1/namespaces/LCUCollections/LCUEmotesEnabled
  /lol-platform-config/v1/namespaces/LCUCollections/LCURunesVisible
  /lol-platform-config/v1/namespaces/LCUCollections/LCUSkinsViewerEnabled
  /lol-platform-config/v1/namespaces/LcuAlphaShutdown
  /lol-platform-config/v1/namespaces/LcuAlphaShutdown/Countdown
  /lol-platform-config/v1/namespaces/LcuAlphaShutdown/Enabled
  /lol-platform-config/v1/namespaces/LcuBuddySpectate
  /lol-platform-config/v1/namespaces/LcuBuddySpectate/Enabled
  /lol-platform-config/v1/namespaces/LcuChampionDetails
  /lol-platform-config/v1/namespaces/LcuChampionDetails/AbilitiesSectionEnabled
  /lol-platform-config/v1/namespaces/LcuChampionDetails/Enabled
  /lol-platform-config/v1/namespaces/LcuChampionDetails/PawEnabled
  /lol-platform-config/v1/namespaces/LcuChampionDetails/SkinsSectionEnabled
  /lol-platform-config/v1/namespaces/LcuChampionSelect
  /lol-platform-config/v1/namespaces/LcuChampionSelect/ChampSelectMuting
  /lol-platform-config/v1/namespaces/LcuChampionSelect/ChampSelectMutingEnabled
  /lol-platform-config/v1/namespaces/LcuChampionSelect/ChampTradingTooltipEnabled
  /lol-platform-config/v1/namespaces/LcuChampionSelect/DisableAutoSmiteAssignment
  /lol-platform-config/v1/namespaces/LcuChampionSelect/DraftActionTickSoundThreshold
  /lol-platform-config/v1/namespaces/LcuChampionSelect/EnableFavorites
  /lol-platform-config/v1/namespaces/LcuChampionSelect/EnablePositionFilters
  /lol-platform-config/v1/namespaces/LcuChampionSelect/IsDisconnectNotificationEnabled
  /lol-platform-config/v1/namespaces/LcuChampionSelect/MinPickIntentDuration
  /lol-platform-config/v1/namespaces/LcuChampionSelect/PickOrderSwappingTooltipEnabled
  /lol-platform-config/v1/namespaces/LcuChampionSelect/PotatoModeForced
  /lol-platform-config/v1/namespaces/LcuChampionSelect/RandomChampionEnabledGameQueues
  /lol-platform-config/v1/namespaces/LcuChampionSelect/RandomChampionRateLimitInterval
  /lol-platform-config/v1/namespaces/LcuChampionSelect/RandomChampionRateLimitMaxActions
  /lol-platform-config/v1/namespaces/LcuChampionSelect/ReportingEnabled
  /lol-platform-config/v1/namespaces/LcuChampionSelect/ShowEmoteButton
  /lol-platform-config/v1/namespaces/LcuChampionSelect/SkinPurchaseEnabled
  /lol-platform-config/v1/namespaces/LcuChampionSelect/SkinPurchaseTime
  /lol-platform-config/v1/namespaces/LcuEmailVerification
  /lol-platform-config/v1/namespaces/LcuEmailVerification/Enabled
  /lol-platform-config/v1/namespaces/LcuEmailVerification/IsOptional
  /lol-platform-config/v1/namespaces/LcuEmailVerification/MaxOptionalLevel
  /lol-platform-config/v1/namespaces/LcuEmailVerification/MinimumSummonerLevel
  /lol-platform-config/v1/namespaces/LcuEmailVerification/RequiredLogins
  /lol-platform-config/v1/namespaces/LcuEsportsSpectator
  /lol-platform-config/v1/namespaces/LcuEsportsSpectator/Enabled
  /lol-platform-config/v1/namespaces/LcuGameSettings
  /lol-platform-config/v1/namespaces/LcuGameSettings/GameplayEnabled
  /lol-platform-config/v1/namespaces/LcuGameSettings/HotkeysEnabled
  /lol-platform-config/v1/namespaces/LcuGameSettings/InterfaceEnabled
  /lol-platform-config/v1/namespaces/LcuGameSettings/SoundEnabled
  /lol-platform-config/v1/namespaces/LcuHome
  /lol-platform-config/v1/namespaces/LcuHome/RequireItemLoaded
  /lol-platform-config/v1/namespaces/LcuHovercard
  /lol-platform-config/v1/namespaces/LcuHovercard/Disabled
  /lol-platform-config/v1/namespaces/LcuLeagueSpectate
  /lol-platform-config/v1/namespaces/LcuLeagueSpectate/Enabled
  /lol-platform-config/v1/namespaces/LcuLobby
  /lol-platform-config/v1/namespaces/LcuLobby/AutoGrantInviteEnabled
  /lol-platform-config/v1/namespaces/LcuLobby/PotatoModeForced
  /lol-platform-config/v1/namespaces/LcuLobby/QueueEligibilityV2Enabled
  /lol-platform-config/v1/namespaces/LcuLobby/SendInventoryTokenMetricsEnabled
  /lol-platform-config/v1/namespaces/LcuLoyalty
  /lol-platform-config/v1/namespaces/LcuLoyalty/LeagueUnlockedEnabled
  /lol-platform-config/v1/namespaces/LcuLoyalty/LolcafeEnabled
  /lol-platform-config/v1/namespaces/LcuNpe
  /lol-platform-config/v1/namespaces/LcuNpe/HardMaxSummonerLevel
  /lol-platform-config/v1/namespaces/LcuNpe/MaxSummonerLevel
  /lol-platform-config/v1/namespaces/LcuNpe/RewardsChallengesEnabled
  /lol-platform-config/v1/namespaces/LcuPayments
  /lol-platform-config/v1/namespaces/LcuPayments/BypassAccountIds
  /lol-platform-config/v1/namespaces/LcuPayments/Host
  /lol-platform-config/v1/namespaces/LcuPayments/PmcEdgeHost
  /lol-platform-config/v1/namespaces/LcuPayments/PmcSessionsEnabled
  /lol-platform-config/v1/namespaces/LcuPayments/RiotPayEnabled
  /lol-platform-config/v1/namespaces/LcuPayments/RiotPayThrottle
  /lol-platform-config/v1/namespaces/LcuProfiles
  /lol-platform-config/v1/namespaces/LcuProfiles/Enabled
  /lol-platform-config/v1/namespaces/LcuPurchaseWidget
  /lol-platform-config/v1/namespaces/LcuPurchaseWidget/AlwaysShowPurchaseDisclaimer
  /lol-platform-config/v1/namespaces/LcuPurchaseWidget/BaseUrl
  /lol-platform-config/v1/namespaces/LcuPurchaseWidget/CapOrdersUrl
  /lol-platform-config/v1/namespaces/LcuPurchaseWidget/Enabled
  /lol-platform-config/v1/namespaces/LcuPurchaseWidget/NonRefundableDisclaimerEnabled
  /lol-platform-config/v1/namespaces/LcuSettings
  /lol-platform-config/v1/namespaces/LcuSocial
  /lol-platform-config/v1/namespaces/LcuSocial/AutoLinkEnabled
  /lol-platform-config/v1/namespaces/LcuSocial/ChatWindowResizeEnabled
  /lol-platform-config/v1/namespaces/LcuSocial/ClearChatHistoryEnabled
  /lol-platform-config/v1/namespaces/LcuSocial/DefaultGameQueues
  /lol-platform-config/v1/namespaces/LcuSocial/EnabledGameQueues
  /lol-platform-config/v1/namespaces/LcuSocial/ForceChatFilter
  /lol-platform-config/v1/namespaces/LcuSocial/FriendRequestToastsDisabled
  /lol-platform-config/v1/namespaces/LcuSocial/FriendsListGiftingEnabled
  /lol-platform-config/v1/namespaces/LcuSocial/MoreUnreadsEnabled
  /lol-platform-config/v1/namespaces/LcuSocial/NewChatButtonEnabled
  /lol-platform-config/v1/namespaces/LcuSocial/RecentlyPlayedDisabled
  /lol-platform-config/v1/namespaces/LcuSocial/SlashMeEnabled
  /lol-platform-config/v1/namespaces/LcuSocial/SortConversationsByTimeEnabled
  /lol-platform-config/v1/namespaces/LcuSocial/StatusesDisabled
  /lol-platform-config/v1/namespaces/LcuSocial/VirtualizedMessagesEnabled
  /lol-platform-config/v1/namespaces/LcuSocial/VirtualizedRosterEnabled
  /lol-platform-config/v1/namespaces/LcuSummonerIconPicker
  /lol-platform-config/v1/namespaces/LcuSummonerIconPicker/Enabled
  /lol-platform-config/v1/namespaces/LcuTft
  /lol-platform-config/v1/namespaces/LcuTft/PatchNotesUrl
  /lol-platform-config/v1/namespaces/LcuTutorial
  /lol-platform-config/v1/namespaces/LcuTutorial/CarouselChampIds
  /lol-platform-config/v1/namespaces/LcuTutorial/Enabled
  /lol-platform-config/v1/namespaces/LcuTutorial/GameModeSelectEnabled
  /lol-platform-config/v1/namespaces/LcuTutorial/IntroABTestPercentage
  /lol-platform-config/v1/namespaces/LcuTutorial/NewPlayerExperienceEnabled
  /lol-platform-config/v1/namespaces/LcuTutorial/SkipTutorialPathAfterLevel
  /lol-platform-config/v1/namespaces/LcuTutorial/StatsTimeout
  /lol-platform-config/v1/namespaces/LcuTutorial/TutorialSummonerIcon
  /lol-platform-config/v1/namespaces/LeagueConfig
  /lol-platform-config/v1/namespaces/LeagueConfig/ApexDemotionNotificationEnabled
  /lol-platform-config/v1/namespaces/LeagueConfig/ChallengerLaddersEnabled
  /lol-platform-config/v1/namespaces/LeagueConfig/ConfigRefreshIntervalSeconds
  /lol-platform-config/v1/namespaces/LeagueConfig/DefaultJwtTimeToLiveSeconds
  /lol-platform-config/v1/namespaces/LeagueConfig/EosNotificationSettingsSchemaVer
  /lol-platform-config/v1/namespaces/LeagueConfig/EosNotificationsConfig
  /lol-platform-config/v1/namespaces/LeagueConfig/EosNotificationsEnabled
  /lol-platform-config/v1/namespaces/LeagueConfig/FlexRestrictionModalEnabled
  /lol-platform-config/v1/namespaces/LeagueConfig/IsGlobalNotificationsEnabled
  /lol-platform-config/v1/namespaces/LeagueConfig/LeagueServiceEnabled
  /lol-platform-config/v1/namespaces/LeagueConfig/RankedReferenceModalEnabled
  /lol-platform-config/v1/namespaces/LeagueEdgeClient
  /lol-platform-config/v1/namespaces/LeagueEdgeClient/Enabled
  /lol-platform-config/v1/namespaces/LeagueEdgeClientEnabledServices
  /lol-platform-config/v1/namespaces/LeagueEdgeClientEnabledServices/GSMv2
  /lol-platform-config/v1/namespaces/LeagueEdgeClientEnabledServices/GameAgnosticMatchHistory
  /lol-platform-config/v1/namespaces/LeagueEdgeClientEnabledServices/Leagues
  /lol-platform-config/v1/namespaces/LeagueEdgeClientEnabledServices/MarketingPreferences
  /lol-platform-config/v1/namespaces/LeagueEdgeClientEnabledServices/Missions
  /lol-platform-config/v1/namespaces/LeagueEdgeClientEnabledServices/Parties
  /lol-platform-config/v1/namespaces/LeagueEdgeClientEnabledServices/Summoner
  /lol-platform-config/v1/namespaces/LeagueEdgeClientEnabledServices/Tastes
  /lol-platform-config/v1/namespaces/LeagueSession/FailureRefreshTimeoutSeconds
  /lol-platform-config/v1/namespaces/LeagueSession/RefreshTokenOverride
  /lol-platform-config/v1/namespaces/LeagueSession/UseSessionRefreshV2
  /lol-platform-config/v1/namespaces/LeaverBuster
  /lol-platform-config/v1/namespaces/LeaverBuster/IsLbsEnabled
  /lol-platform-config/v1/namespaces/LeaverBuster/IsLockoutModalEnabled
  /lol-platform-config/v1/namespaces/Loadouts
  /lol-platform-config/v1/namespaces/Loadouts/EnableStarShardsServices
  /lol-platform-config/v1/namespaces/Loadouts/EnableStarShardsUpgradeFlow
  /lol-platform-config/v1/namespaces/Loadouts/Enabled
  /lol-platform-config/v1/namespaces/Loadouts/UseV4LoadoutFlow
  /lol-platform-config/v1/namespaces/Loadouts/ValidInventoryTypes
  /lol-platform-config/v1/namespaces/LoginDataPacket
  /lol-platform-config/v1/namespaces/LoginDataPacket/simpleMessages
  /lol-platform-config/v1/namespaces/LootConfig
  /lol-platform-config/v1/namespaces/LootConfig/Enabled
  /lol-platform-config/v1/namespaces/LootConfig/EventChestsEnabled
  /lol-platform-config/v1/namespaces/LootConfig/InitializationGoalFlags
  /lol-platform-config/v1/namespaces/LootConfig/LcuEnabled
  /lol-platform-config/v1/namespaces/LootConfig/LootOddsQueryEvaluationEnabled
  /lol-platform-config/v1/namespaces/LootConfig/PurchaseChestsEnabled
  /lol-platform-config/v1/namespaces/Missions
  /lol-platform-config/v1/namespaces/Missions/EligibilityInventoryTypes
  /lol-platform-config/v1/namespaces/Missions/MissionsCompressed
  /lol-platform-config/v1/namespaces/Missions/MissionsCooldownPollingTime
  /lol-platform-config/v1/namespaces/Missions/MissionsEnabled
  /lol-platform-config/v1/namespaces/Missions/MissionsFrontEndEnabled
  /lol-platform-config/v1/namespaces/Missions/MissionsPollingTime
  /lol-platform-config/v1/namespaces/Missions/MissionsTabTrackerEnabled
  /lol-platform-config/v1/namespaces/Missions/MissionsUseV4Api
  /lol-platform-config/v1/namespaces/Missions/SendSimpleInventoryTokens
  /lol-platform-config/v1/namespaces/Mutators
  /lol-platform-config/v1/namespaces/Mutators/CustomGameMutators
  /lol-platform-config/v1/namespaces/Mutators/EnabledAssetMutators
  /lol-platform-config/v1/namespaces/Mutators/EnabledCustomModes
  /lol-platform-config/v1/namespaces/Mutators/EnabledModes
  /lol-platform-config/v1/namespaces/Mutators/EnabledMutators
  /lol-platform-config/v1/namespaces/NewMatchHistory
  /lol-platform-config/v1/namespaces/NewMatchHistory/ACSEndpoint
  /lol-platform-config/v1/namespaces/NewMatchHistory/Enabled
  /lol-platform-config/v1/namespaces/NewMatchHistory/MatchHistoryWebURL
  /lol-platform-config/v1/namespaces/NewMatchHistory/SharingEnabled
  /lol-platform-config/v1/namespaces/NewMatchHistory/TftMatchHistoryEnabled
  /lol-platform-config/v1/namespaces/NewPlayerIntro
  /lol-platform-config/v1/namespaces/NewPlayerIntro/NewSummonerIconIds
  /lol-platform-config/v1/namespaces/Parties
  /lol-platform-config/v1/namespaces/Parties/EnableLobbyCreation
  /lol-platform-config/v1/namespaces/Parties/Enabled
  /lol-platform-config/v1/namespaces/Parties/EnabledForTeamBuilderQueues
  /lol-platform-config/v1/namespaces/Parties/GameflowRegistrationStatusRequired
  /lol-platform-config/v1/namespaces/Parties/LoginRegistrationTimeout
  /lol-platform-config/v1/namespaces/Parties/NotificationDelaySamplingPercentage
  /lol-platform-config/v1/namespaces/Parties/OpenPartyEnable
  /lol-platform-config/v1/namespaces/Parties/PremadeEligibilityFromPartiesEnabled
  /lol-platform-config/v1/namespaces/Parties/PremadeEligibilityQueuesDelayedRefreshTimeoutSeconds
  /lol-platform-config/v1/namespaces/Parties/RegistrationConfigurationChangedTimeout
  /lol-platform-config/v1/namespaces/Parties/RegistrationCredentialsRequired
  /lol-platform-config/v1/namespaces/Parties/RegistrationRetryInterval
  /lol-platform-config/v1/namespaces/Parties/ServiceProxySamplingPercentage
  /lol-platform-config/v1/namespaces/PartyRewards
  /lol-platform-config/v1/namespaces/PartyRewards/Enabled
  /lol-platform-config/v1/namespaces/PartyRewards/GameFlowVisualUpdate
  /lol-platform-config/v1/namespaces/Perks
  /lol-platform-config/v1/namespaces/Perks/MinSummonerLevelUnlockCustomPages
  /lol-platform-config/v1/namespaces/Perks/PerksEnabled
  /lol-platform-config/v1/namespaces/Perks/RestrictedPageNamesEnabled
  /lol-platform-config/v1/namespaces/PersonalizedOffers
  /lol-platform-config/v1/namespaces/PersonalizedOffers/BaseServiceURL
  /lol-platform-config/v1/namespaces/PersonalizedOffers/DataAuthModal
  /lol-platform-config/v1/namespaces/PersonalizedOffers/HubEnabled
  /lol-platform-config/v1/namespaces/PersonalizedOffers/Port
  /lol-platform-config/v1/namespaces/PersonalizedOffers/PromotionEndTime
  /lol-platform-config/v1/namespaces/PersonalizedOffers/PromotionName
  /lol-platform-config/v1/namespaces/PersonalizedOffers/Protocol
  /lol-platform-config/v1/namespaces/PersonalizedOffers/ServicePath
  /lol-platform-config/v1/namespaces/PersonalizedOffers/ShowNavButton
  /lol-platform-config/v1/namespaces/PersonalizedOffers/ThemedBackground
  /lol-platform-config/v1/namespaces/PlatformShutdown/Enabled
  /lol-platform-config/v1/namespaces/PlayerBehavior
  /lol-platform-config/v1/namespaces/PlayerBehavior/CodeOfConductEnabled
  /lol-platform-config/v1/namespaces/PlayerBehavior/ReformCardV2Enabled
  /lol-platform-config/v1/namespaces/PlayerFeedbackTool
  /lol-platform-config/v1/namespaces/PlayerFeedbackTool/BackendUrl
  /lol-platform-config/v1/namespaces/PlayerFeedbackTool/EnableHomeTrigger
  /lol-platform-config/v1/namespaces/PlayerNotification
  /lol-platform-config/v1/namespaces/PlayerNotification/Enabled
  /lol-platform-config/v1/namespaces/PlayerPreferences
  /lol-platform-config/v1/namespaces/PlayerPreferences/Enabled
  /lol-platform-config/v1/namespaces/PlayerPreferences/EnforceHttps
  /lol-platform-config/v1/namespaces/PlayerPreferences/ServiceEndpoint
  /lol-platform-config/v1/namespaces/PlayerPreferences/Version
  /lol-platform-config/v1/namespaces/Postgame
  /lol-platform-config/v1/namespaces/Postgame/ShowPositionDetectionEnabled
  /lol-platform-config/v1/namespaces/ProfileHoverCard
  /lol-platform-config/v1/namespaces/ProfileHoverCard/ACSLookup
  /lol-platform-config/v1/namespaces/ProfileHoverCard/IsEnabled
  /lol-platform-config/v1/namespaces/ProfileHoverCard/IsEnabledForBuddyPanelView
  /lol-platform-config/v1/namespaces/ProfileHoverCard/IsEnabledForChatFriendsList
  /lol-platform-config/v1/namespaces/ProfileHoverCard/IsEnabledForChatGroupChatParticipants
  /lol-platform-config/v1/namespaces/ProfileHoverCard/IsEnabledForClubChatParticipants
  /lol-platform-config/v1/namespaces/ProfileHoverCard/IsEnabledForCustomGameLobby
  /lol-platform-config/v1/namespaces/ProfileHoverCard/IsEnabledForSummonerQuickView
  /lol-platform-config/v1/namespaces/ProfileHoverCard/IsEnabledForTeamBuilderSuggestedPlayers
  /lol-platform-config/v1/namespaces/Profiles
  /lol-platform-config/v1/namespaces/Profiles/SkinsPickerEnabled
  /lol-platform-config/v1/namespaces/PublishingContent
  /lol-platform-config/v1/namespaces/PublishingContent/Enabled
  /lol-platform-config/v1/namespaces/PublishingContent/LocalePreferenceEnabled
  /lol-platform-config/v1/namespaces/PublishingContent/LocalePreferenceOptions
  /lol-platform-config/v1/namespaces/PublishingContent/TftHubCardsUrl
  /lol-platform-config/v1/namespaces/QueueImages
  /lol-platform-config/v1/namespaces/QueueImages/OverrideQueueImage
  /lol-platform-config/v1/namespaces/QueueRestriction
  /lol-platform-config/v1/namespaces/QueueRestriction/AllowablePremadeSizesForQueueId440
  /lol-platform-config/v1/namespaces/QueueRestriction/MaxTierAndDivisionForPremadeSize2QueueId1100
  /lol-platform-config/v1/namespaces/QueueRestriction/MaxTierAndDivisionForPremadeSize2QueueId420
  /lol-platform-config/v1/namespaces/QueueRestriction/MaxTierAndRankForPremadeSize1
  /lol-platform-config/v1/namespaces/QueueRestriction/MaxTierAndRankForPremadeSize1QueueId4
  /lol-platform-config/v1/namespaces/QueueRestriction/MaxTierAndRankForPremadeSize1QueueId410
  /lol-platform-config/v1/namespaces/QueueRestriction/MaxTierAndRankForPremadeSize1QueueId420
  /lol-platform-config/v1/namespaces/QueueRestriction/MaxTierAndRankForPremadeSize1QueueId440
  /lol-platform-config/v1/namespaces/QueueRestriction/MaxTierAndRankForPremadeSize1QueueId470
  /lol-platform-config/v1/namespaces/QueueRestriction/MaxTierAndRankForPremadeSize1QueueId9
  /lol-platform-config/v1/namespaces/QueueRestriction/MaxTierAndRankForPremadeSize2
  /lol-platform-config/v1/namespaces/QueueRestriction/MaxTierAndRankForPremadeSize2QueueId4
  /lol-platform-config/v1/namespaces/QueueRestriction/MaxTierAndRankForPremadeSize2QueueId410
  /lol-platform-config/v1/namespaces/QueueRestriction/MaxTierAndRankForPremadeSize2QueueId420
  /lol-platform-config/v1/namespaces/QueueRestriction/MaxTierAndRankForPremadeSize2QueueId440
  /lol-platform-config/v1/namespaces/QueueRestriction/MaxTierAndRankForPremadeSize2QueueId470
  /lol-platform-config/v1/namespaces/QueueRestriction/MaxTierAndRankForPremadeSize2QueueId9
  /lol-platform-config/v1/namespaces/QueueRestriction/MaxTierAndRankForPremadeSize3
  /lol-platform-config/v1/namespaces/QueueRestriction/MaxTierAndRankForPremadeSize3QueueId410
  /lol-platform-config/v1/namespaces/QueueRestriction/MaxTierAndRankForPremadeSize3QueueId420
  /lol-platform-config/v1/namespaces/QueueRestriction/MaxTierAndRankForPremadeSize3QueueId440
  /lol-platform-config/v1/namespaces/QueueRestriction/MaxTierAndRankForPremadeSize3QueueId470
  /lol-platform-config/v1/namespaces/QueueRestriction/MaxTierAndRankForPremadeSize3QueueId9
  /lol-platform-config/v1/namespaces/QueueRestriction/MaxTierAndRankForPremadeSize4
  /lol-platform-config/v1/namespaces/QueueRestriction/MaxTierAndRankForPremadeSize4QueueId410
  /lol-platform-config/v1/namespaces/QueueRestriction/MaxTierAndRankForPremadeSize4QueueId420
  /lol-platform-config/v1/namespaces/QueueRestriction/MaxTierAndRankForPremadeSize4QueueId440
  /lol-platform-config/v1/namespaces/QueueRestriction/MaxTierAndRankForPremadeSize4QueueId470
  /lol-platform-config/v1/namespaces/QueueRestriction/MaxTierAndRankForPremadeSize4QueueId9
  /lol-platform-config/v1/namespaces/QueueRestriction/MaxTierAndRankForPremadeSize5
  /lol-platform-config/v1/namespaces/QueueRestriction/MaxTierAndRankForPremadeSize5QueueId410
  /lol-platform-config/v1/namespaces/QueueRestriction/MaxTierAndRankForPremadeSize5QueueId420
  /lol-platform-config/v1/namespaces/QueueRestriction/MaxTierAndRankForPremadeSize5QueueId440
  /lol-platform-config/v1/namespaces/QueueRestriction/MaxTierAndRankForPremadeSize5QueueId470
  /lol-platform-config/v1/namespaces/QueueRestriction/MaxTierAndRankForPremadeSize5QueueId9
  /lol-platform-config/v1/namespaces/QueueRestriction/MaxTierForPremadeSize2QueueId1100
  /lol-platform-config/v1/namespaces/QueueRestriction/MaxTierForPremadeSize2QueueId420
  /lol-platform-config/v1/namespaces/QueueRestriction/QueuesRequiringTwentyChampions
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedDuoQueueDefaultUnseededTier
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedDuoQueueDefaultUnseededTierQueueId11
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedDuoQueueDefaultUnseededTierQueueId4
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedDuoQueueDefaultUnseededTierQueueId410
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedDuoQueueDefaultUnseededTierQueueId411
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedDuoQueueDefaultUnseededTierQueueId412
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedDuoQueueDefaultUnseededTierQueueId420
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedDuoQueueDefaultUnseededTierQueueId421
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedDuoQueueDefaultUnseededTierQueueId422
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedDuoQueueDefaultUnseededTierQueueId440
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedDuoQueueDefaultUnseededTierQueueId441
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedDuoQueueDefaultUnseededTierQueueId442
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedDuoQueueDefaultUnseededTierQueueId470
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedDuoQueueDefaultUnseededTierQueueId9
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedDuoQueueRestrictionMaxDelta
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedDuoQueueRestrictionMode
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedHighMmrPremadeMaxSize
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedHighMmrPremadeRank
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedHighMmrPremadeRestrictionEnabled
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedHighMmrPremadeTier
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedHighSkillLowestTier
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedHighSkillLowestTierQueueId11
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedHighSkillLowestTierQueueId4
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedHighSkillLowestTierQueueId410
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedHighSkillLowestTierQueueId411
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedHighSkillLowestTierQueueId412
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedHighSkillLowestTierQueueId420
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedHighSkillLowestTierQueueId421
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedHighSkillLowestTierQueueId422
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedHighSkillLowestTierQueueId440
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedHighSkillLowestTierQueueId441
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedHighSkillLowestTierQueueId442
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedHighSkillLowestTierQueueId470
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedHighSkillLowestTierQueueId9
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedHighSkillRestrictionMaxDelta
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedHighSkillRestrictionMaxDeltaQueueId11
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedHighSkillRestrictionMaxDeltaQueueId4
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedHighSkillRestrictionMaxDeltaQueueId410
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedHighSkillRestrictionMaxDeltaQueueId411
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedHighSkillRestrictionMaxDeltaQueueId412
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedHighSkillRestrictionMaxDeltaQueueId420
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedHighSkillRestrictionMaxDeltaQueueId421
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedHighSkillRestrictionMaxDeltaQueueId422
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedHighSkillRestrictionMaxDeltaQueueId440
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedHighSkillRestrictionMaxDeltaQueueId441
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedHighSkillRestrictionMaxDeltaQueueId442
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedHighSkillRestrictionMaxDeltaQueueId470
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedHighSkillRestrictionMaxDeltaQueueId9
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedHighSkillRestrictionMode
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedHighSkillRestrictionModeQueueId11
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedHighSkillRestrictionModeQueueId4
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedHighSkillRestrictionModeQueueId410
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedHighSkillRestrictionModeQueueId411
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedHighSkillRestrictionModeQueueId412
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedHighSkillRestrictionModeQueueId420
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedHighSkillRestrictionModeQueueId421
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedHighSkillRestrictionModeQueueId422
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedHighSkillRestrictionModeQueueId440
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedHighSkillRestrictionModeQueueId441
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedHighSkillRestrictionModeQueueId442
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedHighSkillRestrictionModeQueueId470
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedHighSkillRestrictionModeQueueId9
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedLowSkillRestrictionMaxDelta
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedLowSkillRestrictionMaxDeltaQueueId11
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedLowSkillRestrictionMaxDeltaQueueId4
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedLowSkillRestrictionMaxDeltaQueueId410
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedLowSkillRestrictionMaxDeltaQueueId411
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedLowSkillRestrictionMaxDeltaQueueId412
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedLowSkillRestrictionMaxDeltaQueueId420
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedLowSkillRestrictionMaxDeltaQueueId421
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedLowSkillRestrictionMaxDeltaQueueId422
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedLowSkillRestrictionMaxDeltaQueueId440
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedLowSkillRestrictionMaxDeltaQueueId441
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedLowSkillRestrictionMaxDeltaQueueId442
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedLowSkillRestrictionMaxDeltaQueueId470
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedLowSkillRestrictionMaxDeltaQueueId9
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedLowSkillRestrictionMode
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedLowSkillRestrictionModeQueueId11
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedLowSkillRestrictionModeQueueId4
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedLowSkillRestrictionModeQueueId410
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedLowSkillRestrictionModeQueueId411
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedLowSkillRestrictionModeQueueId412
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedLowSkillRestrictionModeQueueId420
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedLowSkillRestrictionModeQueueId421
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedLowSkillRestrictionModeQueueId422
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedLowSkillRestrictionModeQueueId440
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedLowSkillRestrictionModeQueueId441
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedLowSkillRestrictionModeQueueId442
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedLowSkillRestrictionModeQueueId470
  /lol-platform-config/v1/namespaces/QueueRestriction/RankedLowSkillRestrictionModeQueueId9
  /lol-platform-config/v1/namespaces/QueueRestriction/ServiceEnabled
  /lol-platform-config/v1/namespaces/QueueRewards
  /lol-platform-config/v1/namespaces/QueueRewards/SoloAutoFillProtectionForQueueId440
  /lol-platform-config/v1/namespaces/QueueRewards/SoloIpRewardsForQueueId440
  /lol-platform-config/v1/namespaces/Regalia
  /lol-platform-config/v1/namespaces/Replays
  /lol-platform-config/v1/namespaces/Replays/MinutesUntilReplayConsideredLost
  /lol-platform-config/v1/namespaces/Rewards
  /lol-platform-config/v1/namespaces/Rewards/Enabled
  /lol-platform-config/v1/namespaces/Sanitizer
  /lol-platform-config/v1/namespaces/SkinsViewer
  /lol-platform-config/v1/namespaces/SkinsViewer/DisableAllPurchase
  /lol-platform-config/v1/namespaces/SocialLeaderboard
  /lol-platform-config/v1/namespaces/SocialLeaderboard/IsSocialLeaderboardEnabled
  /lol-platform-config/v1/namespaces/SocialLeaderboard/MinsTillCacheExpiry
  /lol-platform-config/v1/namespaces/SocialLeaderboard/SecsTillAvailabilityCacheExpiry
  /lol-platform-config/v1/namespaces/Spectator
  /lol-platform-config/v1/namespaces/Spectator/SaveReconnectInfoEnabled
  /lol-platform-config/v1/namespaces/SuggestedPlayers
  /lol-platform-config/v1/namespaces/SuggestedPlayers/Enabled
  /lol-platform-config/v1/namespaces/SuggestedPlayers/FriendsOfFriendsEnabled
  /lol-platform-config/v1/namespaces/SuggestedPlayers/MaxNumReplacements
  /lol-platform-config/v1/namespaces/SuggestedPlayers/MaxNumSuggestedPlayers
  /lol-platform-config/v1/namespaces/SuggestedPlayers/OnlineFriendsLimit
  /lol-platform-config/v1/namespaces/Summoner/ConfigRefreshIntervalSeconds
  /lol-platform-config/v1/namespaces/Summoner/JWTMaxTimeoutSeconds
  /lol-platform-config/v1/namespaces/Summoner/JWTMinTimeoutSeconds
  /lol-platform-config/v1/namespaces/Summoner/SummonerProfileCacheEnabled
  /lol-platform-config/v1/namespaces/TeamBuilderDraft
  /lol-platform-config/v1/namespaces/TeamBuilderDraft/EnableChampionSelectPreferences
  /lol-platform-config/v1/namespaces/TeamBuilderDraft/LogAllLCDSMessages
  /lol-platform-config/v1/namespaces/TeamBuilderDraft/SendAfkCheckMetricsEnabled
  /lol-platform-config/v1/namespaces/TeamBuilderDraft/ServiceCallTimeoutMillis
  /lol-platform-config/v1/namespaces/TencentAntiAddiction
  /lol-platform-config/v1/namespaces/TencentAntiAddiction/AntiAddictionUrl
  /lol-platform-config/v1/namespaces/TencentAntiAddiction/Enabled
  /lol-platform-config/v1/namespaces/Trophies
  /lol-platform-config/v1/namespaces/Trophies/IsEnabledOnProfile
  /lol-platform-config/v1/namespaces/Trophies/IsOtherSummonersProfileEnabled
  /lol-platform-config/v1/namespaces/Voice
  /lol-platform-config/v1/namespaces/Voice/Enabled
  /lol-platform-config/v1/namespaces/WardSkinConfig
  /lol-platform-config/v1/namespaces/WardSkinConfig/UseLoadouts
  /lol-platform-config/v1/namespaces/WardSkinConfig/WardSkinSelection

## lol-player-behavior  (3)
  /lol-player-behavior/v1/config
  /lol-player-behavior/v2/reporter-feedback
  /lol-player-behavior/v3/reform-cards

## lol-player-preferences  (1)
  /lol-player-preferences/v1/player-preferences-ready

## lol-player-report-sender  (1)
  /lol-player-report-sender/v1/in-game-reports

## lol-pre-end-of-game  (1)
  /lol-pre-end-of-game/v1/currentSequenceEvent

## lol-premade-voice  (6)
  /lol-premade-voice/v1/availability
  /lol-premade-voice/v1/capturedevices
  /lol-premade-voice/v1/first-experience
  /lol-premade-voice/v1/parental-controls-status
  /lol-premade-voice/v1/participant-records
  /lol-premade-voice/v1/settings

## lol-progression  (2)
  /lol-progression/v1/groups
  /lol-progression/v1/ready

## lol-publishing-content  (3)
  /lol-publishing-content/v1/listeners
  /lol-publishing-content/v1/ready
  /lol-publishing-content/v1/settings

## lol-purchase-widget  (2)
  /lol-purchase-widget/v1/configuration
  /lol-purchase-widget/v3/purchase-offer-order-statuses

## lol-ranked  (9)   <== relevante
  /lol-ranked/v1/cached-ranked-stats
  /lol-ranked/v1/challenger-ladders-enabled
  /lol-ranked/v1/current-lp-change-notification
  /lol-ranked/v1/current-ranked-stats
  /lol-ranked/v1/global-notifications
  /lol-ranked/v1/notifications
  /lol-ranked/v1/ranked-stats
  /lol-ranked/v1/signed-ranked-stats
  /lol-ranked/v1/top-rated-ladders-enabled

## lol-regalia  (2)   <== relevante
  /lol-regalia/v2/config
  /lol-regalia/v2/summoners

## lol-remedy  (1)
  /lol-remedy/v1/remedy-notifications

## lol-replays  (3)
  /lol-replays/v1/configuration
  /lol-replays/v1/metadata
  /lol-replays/v1/rofls

## lol-rewards  (2)
  /lol-rewards/v1/grants
  /lol-rewards/v1/groups

## lol-rms  (1)
  /lol-rms/v1/champion-mastery-leaveup-update

## lol-rso-auth  (2)
  /lol-rso-auth/configuration/v3
  /lol-rso-auth/v1/authorization

## lol-sanctum  (2)
  /lol-sanctum/v1/banners
  /lol-sanctum/v1/ready

## lol-seasons  (1)
  /lol-seasons/v1/season

## lol-service-status  (1)
  /lol-service-status/v1/ticker-messages

## lol-settings  (6)
  /lol-settings/v1/account
  /lol-settings/v1/local
  /lol-settings/v2/account
  /lol-settings/v2/config
  /lol-settings/v2/local
  /lol-settings/v2/ready

## lol-shoppefront  (2)
  /lol-shoppefront/v1/ready
  /lol-shoppefront/v1/stores

## lol-simple-dialog-messages  (1)
  /lol-simple-dialog-messages/v1/messages

## lol-spectator  (1)   <== relevante
  /lol-spectator/v1/spectate

## lol-statstones  (1)
  /lol-statstones/v2/player-summary-self

## lol-store  (2)   <== relevante
  /lol-store/v1/getStoreUrl
  /lol-store/v1/store-ready

## lol-suggested-players  (1)
  /lol-suggested-players/v1/suggested-players

## lol-summoner  (6)   <== relevante
  /lol-summoner/v1/current-summoner
  /lol-summoner/v1/player-alias-state
  /lol-summoner/v1/player-name-mode
  /lol-summoner/v1/status
  /lol-summoner/v1/summoner-requests-ready
  /lol-summoner/v1/summoners

## lol-summoner-profiles  (5)
  /lol-summoner-profiles/v1/get-champion-mastery-view
  /lol-summoner-profiles/v1/get-honor-view
  /lol-summoner-profiles/v1/get-privacy-view
  /lol-summoner-profiles/v1/get-restriction-view
  /lol-summoner-profiles/v1/get-summoner-level-view

## lol-tastes  (1)
  /lol-tastes/v1/ready

## lol-tft  (1)
  /lol-tft/v1/tft

## lol-tft-pass  (6)
  /lol-tft-pass/v1/active-passes
  /lol-tft-pass/v1/battle-pass
  /lol-tft-pass/v1/config-fetched
  /lol-tft-pass/v1/pm-ultimate-victory-pass
  /lol-tft-pass/v1/ready
  /lol-tft-pass/v1/skill-tree-pass

## lol-tft-team-planner  (5)
  /lol-tft-team-planner/v1/config
  /lol-tft-team-planner/v1/ftue
  /lol-tft-team-planner/v1/previous-context
  /lol-tft-team-planner/v1/set
  /lol-tft-team-planner/v2/reminders

## lol-tft-troves  (2)
  /lol-tft-troves/v1/config
  /lol-tft-troves/v1/milestones-group-id

## lol-vanguard  (3)
  /lol-vanguard/v1/notification
  /lol-vanguard/v1/service-session-check-failure
  /lol-vanguard/v1/session

## lol-yourshop  (3)
  /lol-yourshop/v1/modal
  /lol-yourshop/v1/ready
  /lol-yourshop/v1/status

## loyalty  (1)
  /loyalty/v1/loyalty-resource

## mailbox  (1)
  /mailbox/v1/check-new-mail

## memory  (1)
  /memory/v1/fe-processes-ready

## patcher  (3)
  /patcher/v1/notifications
  /patcher/v1/products
  /patcher/v1/status

## platform-ui  (1)
  /platform-ui/v1/discord-link

## player-account  (1)
  /player-account/aliases/v1

## player-notifications  (1)
  /player-notifications/v1/notifications

## player-reporting  (1)
  /player-reporting/v1/reporter-feedback

## plugin-manager  (2)
  /plugin-manager/v1/external-plugins
  /plugin-manager/v1/status

## process-control  (1)
  /process-control/v1/process

## product-metadata  (1)
  /product-metadata/v2/products

## product-session  (1)
  /product-session/v1/external-sessions

## riot-messaging-service  (4)
  /riot-messaging-service/v1/message
  /riot-messaging-service/v1/out-of-sync
  /riot-messaging-service/v1/session
  /riot-messaging-service/v1/state

## riotclient  (10)
  /riotclient/affinity
  /riotclient/app-port
  /riotclient/new-args
  /riotclient/pre-shutdown/begin
  /riotclient/region-locale
  /riotclient/system-info/v1
  /riotclient/ux-crash-count
  /riotclient/ux-state/request
  /riotclient/v1/crash-reporting
  /riotclient/zoom-scale

## rso-auth  (4)
  /rso-auth/configuration/v3
  /rso-auth/v1/session
  /rso-auth/v1/userinfo
  /rso-auth/v2/authorizations

## sanitizer  (1)
  /sanitizer/v1/status

## scd  (1)
  /scd/v1/cookies

## social  (5)
  /social/v1/blocklist
  /social/v1/presences
  /social/v1/ready
  /social/v2/friendrequests
  /social/v4/friends

## system  (1)
  /system/v1/builds

## voice-chat  (5)
  /voice-chat/v1/audio-properties
  /voice-chat/v2/devices
  /voice-chat/v2/state
  /voice-chat/v3/sessions
  /voice-chat/v3/settings