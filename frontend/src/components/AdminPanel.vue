<template>
  <div class="page">
    <h2>Admin Panel — User Management</h2>
    <!-- VULNERABLE #11: This page calls /api/admin/users which has no role check on server -->
    <!-- Any authenticated user can navigate here and see all users -->
    <p class="warn">
      Note: Admin check is client-side only (reads localStorage role).
      Server endpoint /api/admin/users has NO role enforcement.
    </p>

    <div class="card">
      <table>
        <thead>
          <tr>
            <th>ID</th><th>Username</th><th>Email</th><th>Role</th>
            <th>Password Hash</th><th>API Key</th><th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in users" :key="u.id">
            <td>{{ u.id }}</td>
            <td>{{ u.username }}</td>
            <td>{{ u.email }}</td>
            <td>
              <!-- VULNERABLE #12: Role can be changed directly in UI -->
              <select v-model="u.role" @change="updateUser(u)">
                <option value="user">user</option>
                <option value="admin">admin</option>
              </select>
            </td>
            <!-- VULNERABLE #16: Password hash shown in admin table -->
            <td><code class="hash">{{ u.password }}</code></td>
            <!-- VULNERABLE #17: API key shown in plain text -->
            <td><code class="apikey">{{ u.api_key }}</code></td>
            <td><button @click="updateUser(u)" class="btn-sm">Save</button></td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

const API = `http://${window.location.hostname}:50000`

export default {
  name: 'AdminPanel',
  data() {
    return { users: [] }
  },
  async mounted() {
    // VULNERABLE #11: Calls /api/admin/users — server does NOT check role
    const res = await axios.get(`${API}/api/admin/users`, {
      headers: { Authorization: 'Bearer ' + localStorage.getItem('token') },
    })
    this.users = res.data
  },
  methods: {
    async updateUser(user) {
      // VULNERABLE #12: Mass assignment — sends role to /api/users/{id} which accepts it
      await axios.put(
        `${API}/api/users/${user.id}`,
        { email: user.email, role: user.role, api_key: user.api_key },
        { headers: { Authorization: 'Bearer ' + localStorage.getItem('token') } },
      )
      alert(`User ${user.username} updated`)
    },
  },
}
</script>

<style scoped>
.page { padding:24px; max-width:1200px; margin:0 auto; }
h2 { color:#1a237e; margin-bottom:8px; }
.warn { background:#fff3e0; border-left:4px solid #ff6f00; padding:10px 14px; border-radius:4px; margin-bottom:16px; font-size:.9em; color:#e65100; }
.card { background:white; border-radius:10px; padding:20px; box-shadow:0 2px 8px rgba(0,0,0,.08); }
table { width:100%; border-collapse:collapse; }
th { text-align:left; padding:10px; background:#f5f5f5; color:#555; font-weight:600; font-size:.85em; }
td { padding:10px; border-bottom:1px solid #f0f0f0; font-size:.85em; }
code.hash { background:#fce4ec; color:#c62828; padding:2px 6px; border-radius:4px; font-size:.8em; }
code.apikey { background:#e8f5e9; color:#2e7d32; padding:2px 6px; border-radius:4px; font-size:.8em; }
select { padding:4px 8px; border:1px solid #ddd; border-radius:4px; }
.btn-sm { background:#1a237e; color:white; border:none; padding:4px 12px; border-radius:4px; cursor:pointer; font-size:.85em; }
</style>
