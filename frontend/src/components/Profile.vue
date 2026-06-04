<template>
  <div class="page">
    <h2>My Profile</h2>

    <div class="card" v-if="user">
      <div class="profile-grid">
        <div class="field">
          <label>User ID</label>
          <p>{{ user.id }}</p>
        </div>
        <div class="field">
          <label>Username</label>
          <p>{{ user.username }}</p>
        </div>
        <div class="field">
          <label>Email</label>
          <input v-model="editEmail" />
        </div>
        <div class="field">
          <!-- VULNERABLE #12: User can change their own role -->
          <label>Role</label>
          <select v-model="editRole">
            <option value="user">user</option>
            <option value="admin">admin</option>   <!-- VULNERABLE #12: Privilege escalation -->
          </select>
        </div>
      </div>

      <!-- VULNERABLE #16: Password hash displayed to user -->
      <div class="sensitive-info">
        <label>Password Hash (MD5)</label>
        <code>{{ user.password }}</code>
      </div>

      <!-- VULNERABLE #17: API key shown in profile page, stored in localStorage -->
      <div class="sensitive-info">
        <label>Your API Key</label>
        <code>{{ user.api_key }}</code>
      </div>

      <div class="localStorage-dump">
        <label>localStorage Contents (Debug)</label>
        <!-- VULNERABLE #17: Dumps all localStorage including token, role, api_key -->
        <pre>{{ localStorageDump }}</pre>
      </div>

      <button @click="saveProfile" class="btn-primary">Save Profile</button>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

const API = `http://${window.location.hostname}:50000`

export default {
  name: 'Profile',
  data() {
    return {
      user:       null,
      editEmail:  '',
      editRole:   'user',
    }
  },
  computed: {
    localStorageDump() {
      // VULNERABLE #17: Exposes all sensitive localStorage data
      const dump = {}
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i)
        dump[key] = localStorage.getItem(key)
      }
      return JSON.stringify(dump, null, 2)
    },
  },
  async mounted() {
    // VULNERABLE #16: /api/me returns password hash + api_key
    const res = await axios.get(`${API}/api/me`, {
      headers: { Authorization: 'Bearer ' + localStorage.getItem('token') },
    })
    this.user      = res.data
    this.editEmail = res.data.email
    this.editRole  = res.data.role
  },
  methods: {
    async saveProfile() {
      const userId = localStorage.getItem('user_id')
      // VULNERABLE #12: Sends role field — server accepts it (mass assignment)
      await axios.put(
        `${API}/api/users/${userId}`,
        { email: this.editEmail, role: this.editRole },
        { headers: { Authorization: 'Bearer ' + localStorage.getItem('token') } },
      )
      // VULNERABLE #17: Update role in localStorage
      localStorage.setItem('role', this.editRole)
      alert('Profile updated!')
      location.reload()
    },
  },
}
</script>

<style scoped>
.page { padding:24px; max-width:800px; margin:0 auto; }
h2 { color:#1a237e; margin-bottom:16px; }
.card { background:white; border-radius:10px; padding:24px; box-shadow:0 2px 8px rgba(0,0,0,.08); }
.profile-grid { display:grid; grid-template-columns:repeat(2,1fr); gap:20px; margin-bottom:20px; }
.field label { font-size:.8em; color:#888; margin-bottom:4px; display:block; }
.field input, .field select {
  width:100%; padding:8px 12px; border:1px solid #ddd; border-radius:6px; font-size:1em;
}
.sensitive-info { margin-bottom:16px; }
.sensitive-info label { font-size:.8em; color:#888; margin-bottom:4px; display:block; }
.sensitive-info code {
  display:block; background:#fce4ec; color:#c62828; padding:8px 12px;
  border-radius:6px; font-size:.85em; word-break:break-all;
}
.localStorage-dump { margin-bottom:20px; }
.localStorage-dump label { font-size:.8em; color:#888; margin-bottom:4px; display:block; }
.localStorage-dump pre {
  background:#f5f5f5; padding:12px; border-radius:6px;
  font-size:.8em; overflow-x:auto; max-height:200px; overflow-y:auto;
}
.btn-primary { background:#1a237e; color:white; border:none; padding:10px 24px; border-radius:6px; cursor:pointer; }
</style>
