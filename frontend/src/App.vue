<template>
  <div id="app">
    <nav class="navbar">
      <div class="nav-brand">Contract Portal</div>
      <div class="nav-links">
        <router-link to="/dashboard">Dashboard</router-link>
        <router-link to="/contracts">Contracts</router-link>
        <router-link to="/admin">Admin</router-link>
        <router-link to="/profile">Profile</router-link>
      </div>
    </nav>
    <router-view />
  </div>
</template>

<script>
export default {
  name: 'App',
  computed: {
    isLoggedIn() {
      return !!localStorage.getItem('token')   // VULNERABLE #17
    },
    username() {
      return localStorage.getItem('username')  // VULNERABLE #17
    },
    userRole() {
      return localStorage.getItem('role')      // VULNERABLE #17: role from localStorage
    },
  },
  methods: {
    logout() {
      // Clears localStorage on logout (but token never actually expires on server)
      localStorage.removeItem('token')
      localStorage.removeItem('username')
      localStorage.removeItem('role')
      localStorage.removeItem('api_key')
      this.$router.push('/')
    },
  },
}
</script>

<style>
.navbar {
  display: flex; align-items: center; gap: 16px;
  background: #1a237e; color: white; padding: 12px 24px;
}
.nav-brand { font-size: 1.2em; font-weight: bold; margin-right: auto; }
.nav-links a { color: #90caf9; text-decoration: none; padding: 4px 10px; border-radius: 4px; }
.nav-links a:hover, .nav-links a.router-link-active { background: #283593; color: white; }
.btn-logout { background: #c62828; color: white; border: none; padding: 4px 12px; border-radius: 4px; cursor: pointer; }
.user-badge { font-size: 0.8em; background: #283593; padding: 4px 10px; border-radius: 12px; }
</style>
