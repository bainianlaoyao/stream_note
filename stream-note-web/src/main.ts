import { createApp } from 'vue'
import router from './router'
import App from './App.vue'
import { pinia } from './stores/pinia'
import './assets/styles/base.css'

const app = createApp(App)

app.use(pinia)
app.use(router)

app.mount('#app')
