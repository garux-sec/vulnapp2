<template>
  <div class="login-wrap">
    <div class="login-card">
      <h1>Contract Portal</h1>
      <p class="subtitle">Internal System</p>

      <form @submit.prevent="doLogin">
        <div class="field">
          <label>Username</label>
          <input v-model="username" type="text" placeholder="username" autocomplete="off" />
        </div>
        <div class="field">
          <label>Password</label>
          <input v-model="password" type="password" placeholder="password" />
        </div>
        <!-- VULNERABLE #6 & #7: No CAPTCHA, no lockout UI, no rate limit -->
        <button type="submit" :disabled="loading">
          {{ loading ? 'Logging in...' : 'Login' }}
        </button>
      </form>

      <p v-if="error" class="error">{{ error }}</p>

      <div class="forgot">
        <a href="#" @click.prevent="showForgot = !showForgot">Forgot password?</a>
      </div>

      <div v-if="showForgot" class="forgot-form">
        <input v-model="forgotEmail" type="email" placeholder="Enter your email" />
        <button @click="doForgotPassword">Send Reset Link</button>
        <!-- VULNERABLE #8: Token shown directly in UI (from debug_token in response) -->
        <p v-if="resetToken" class="debug-info">
          [DEBUG] Reset token: <strong>{{ resetToken }}</strong>
        </p>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

const API = `http://${window.location.hostname}:50000`

export default {
  name: 'Login',
  data() {
    return {
      username:   '',
      password:   '',
      loading:    false,
      error:      '',
      showForgot: false,
      forgotEmail:'',
      resetToken: '',
    }
  },
  methods: {
    async doLogin() {
      this.loading = true
      this.error   = ''
      try {
        // VULNERABLE #6 & #7: Unlimited login attempts, no lockout
        const res = await axios.post(`${API}/api/login`, {
          username: this.username,
          password: this.password,
        })

        const { token, user } = res.data

        // VULNERABLE #17: Sensitive data stored in localStorage
        localStorage.setItem('token',   token)
        localStorage.setItem('username',user.username)
        localStorage.setItem('role',    user.role)       // role stored client-side
        localStorage.setItem('api_key', user.api_key)    // VULNERABLE #17: API key in localStorage
        localStorage.setItem('user_id', user.id)

        this.$router.push('/dashboard')
      } catch (e) {
        this.error = e.response?.data?.detail || 'Login failed'
      } finally {
        this.loading = false
      }
    },

    async doForgotPassword() {
      try {
        const res = await axios.post(`${API}/api/forgot-password`, {
          email: this.forgotEmail,
        })
        // VULNERABLE #8: Show debug token from response
        this.resetToken = res.data.debug_token
      } catch (e) {
        alert('Error: ' + (e.response?.data?.detail || e.message))
      }
    },
  },
}
</script>

<style scoped>
.login-wrap {
  min-height: 100vh; display: flex; align-items: center;
  justify-content: center; background: linear-gradient(135deg, #1a237e, #283593);
}
.login-card {
  background: white; border-radius: 12px; padding: 40px;
  width: 380px; box-shadow: 0 8px 32px rgba(0,0,0,.2);
}
h1 { color: #1a237e; margin-bottom: 4px; }
.subtitle { color: #666; margin-bottom: 24px; font-size: .9em; }
.field { margin-bottom: 16px; }
.field label { display: block; margin-bottom: 6px; font-weight: 500; color: #333; }
.field input {
  width: 100%; padding: 10px 12px; border: 1px solid #ddd;
  border-radius: 6px; font-size: 1em;
}
button[type=submit] {
  width: 100%; padding: 12px; background: #1a237e; color: white;
  border: none; border-radius: 6px; font-size: 1em; cursor: pointer;
}
.error { color: #c62828; margin-top: 12px; font-size: .9em; }
.forgot { margin-top: 16px; text-align: center; }
.forgot a { color: #1a237e; font-size: .9em; }
.forgot-form { margin-top: 12px; display: flex; flex-direction: column; gap: 8px; }
.forgot-form input { padding: 8px; border: 1px solid #ddd; border-radius: 6px; }
.forgot-form button { padding: 8px; background: #283593; color: white; border: none; border-radius: 6px; cursor: pointer; }
.debug-info { background: #fff3e0; padding: 8px; border-radius: 4px; font-size: .85em; }
</style>
