import type { CapacitorConfig } from '@capacitor/cli'

const config: CapacitorConfig = {
  appId: 'com.streamnote.app',
  appName: 'Stream Note',
  webDir: 'dist',
  bundledWebRuntime: false,
  server: {
    hostname: 'localhost',
    androidScheme: 'http',
    cleartext: true
  },
  android: {
    allowMixedContent: true
  }
}

export default config
