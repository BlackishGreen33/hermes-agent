import { SETTINGS_MANIFEST } from './settings-manifest'
import type { SettingsSubpage } from './subpages'

// Pages with separate tasks expose content-only subpages. Billing keeps its
// existing capability-gated bview=overview|plans flow rather than adding a
// second route parameter that could disagree with a pending financial action.
export const OTHER_SUBPAGES: Record<string, SettingsSubpage[]> = {
  gateway: [
    { id: 'connection', labelKey: 'gatewayConnection' },
    { id: 'devices', labelKey: 'gatewayDevices' },
    { id: 'managed-updates', labelKey: 'gatewayManagedUpdates' }
  ],
  keybinds: [
    { id: 'shortcuts', labelKey: 'keyboardShortcuts' },
    { available: SETTINGS_MANIFEST.keybinds.hudModifier.available, id: 'hud-gesture', labelKey: 'hudGesture' },
    { available: SETTINGS_MANIFEST.keybinds.screenshot.available, id: 'screen-capture', labelKey: 'screenCapture' }
  ],
  notifications: [
    { id: 'alerts', labelKey: 'notificationAlerts' },
    { id: 'sounds', labelKey: 'notificationSounds' }
  ],
  sessions: [
    { id: 'archived', labelKey: 'archivedSessions' },
    { id: 'default-directory', labelKey: 'defaultDirectory' }
  ],
  vault: [
    { id: 'credentials', labelKey: 'vaultCredentials' },
    { id: 'sources', labelKey: 'vaultSources' }
  ],
  about: [
    { id: 'updates', labelKey: 'appUpdates' },
    { id: 'uninstall', labelKey: 'uninstall' }
  ]
}
