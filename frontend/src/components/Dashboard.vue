<template>
  <div class="dashboard">
    <div class="hero">
      <!-- VULNERABLE #13: DOM-based XSS via innerHTML — welcome message from URL hash -->
      <h2 ref="welcomeRef">Welcome</h2>
      <p class="api-key-display">
        Your API Key: <code>{{ apiKey }}</code>
        <!-- VULNERABLE #17 & #19: API key from localStorage displayed in UI -->
      </p>
    </div>

    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-num">{{ contracts.length }}</div>
        <div class="stat-label">Total Contracts</div>
      </div>
      <div class="stat-card">
        <div class="stat-num">{{ pending }}</div>
        <div class="stat-label">Pending Approval</div>
      </div>
      <div class="stat-card">
        <div class="stat-num">{{ approved }}</div>
        <div class="stat-label">Approved</div>
      </div>
      <div class="stat-card">
        <div class="stat-num">${{ totalValue.toLocaleString() }}</div>
        <div class="stat-label">Total Value</div>
      </div>
    </div>

    <div class="search-bar">
      <input v-model="searchQ" placeholder="Search contracts..." @input="doSearch" />
      <!-- VULNERABLE #15: q param sent directly to SQL LIKE without sanitization -->
    </div>

    <div v-if="searchResults" class="search-results">
      <h3>Search Results</h3>
      <!-- VULNERABLE #13: DOM XSS — search query reflected via innerHTML -->
      <p>Results for: <span ref="searchLabel"></span></p>
      <div v-for="r in searchResults" :key="r.id" class="result-item">
        {{ r.title }} — ${{ r.amount }}
      </div>
    </div>

    <div class="recent-contracts">
      <h3>Recent Contracts</h3>
      <div v-for="c in contracts.slice(0,5)" :key="c.id" class="contract-row"
           @click="$router.push('/contracts/' + c.id)">
        <span class="ct-title">{{ c.title }}</span>
        <span :class="'badge badge-' + c.status">{{ c.status }}</span>
        <span class="ct-amount">${{ c.amount?.toLocaleString() }}</span>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

const API = `http://${window.location.hostname}:50000`

// VULNERABLE #19: Hardcoded API key in frontend source
const HARDCODED_PAYMENT_API_KEY = 'pk_live_corp_payment_abc123xyz456secret'

export default {
  name: 'Dashboard',
  data() {
    return {
      contracts:     [],
      searchQ:       '',
      searchResults: null,
      // VULNERABLE #17: API key read from localStorage
      apiKey: localStorage.getItem('api_key'),
    }
  },
  computed: {
    pending()    { return this.contracts.filter(c => c.status === 'pending').length },
    approved()   { return this.contracts.filter(c => c.status === 'approved').length },
    totalValue() { return this.contracts.reduce((s, c) => s + (c.amount || 0), 0) },
  },
  async mounted() {
    await this.loadContracts()

    // VULNERABLE #13: DOM-based XSS
    // URL: /#<img src=x onerror=alert(document.cookie)>
    const hash = decodeURIComponent(window.location.hash.slice(1))
    if (hash) {
      // VULNERABLE #13: unsanitized user-controlled value written to DOM
      this.$refs.welcomeRef.innerHTML = 'Welcome, ' + hash
    }

    // Log hardcoded key to console (also visible in source map)
    console.log('[DEBUG] Payment API Key:', HARDCODED_PAYMENT_API_KEY)
  },
  methods: {
    async loadContracts() {
      const res = await axios.get(`${API}/api/contracts`, {
        headers: { Authorization: 'Bearer ' + localStorage.getItem('token') },
      })
      this.contracts = res.data
    },
    async doSearch() {
      if (!this.searchQ) { this.searchResults = null; return }
      try {
        const res = await axios.get(`${API}/api/search`, {
          params: { q: this.searchQ },
          headers: { Authorization: 'Bearer ' + localStorage.getItem('token') },
        })
        this.searchResults = res.data.results

        // VULNERABLE #13: DOM XSS — search query injected via innerHTML
        if (this.$refs.searchLabel) {
          this.$refs.searchLabel.innerHTML = this.searchQ
        }
      } catch (e) {
        console.error(e)
      }
    },
  },
}
</script>

<style scoped>
.dashboard { padding: 24px; max-width: 1100px; margin: 0 auto; }
.hero { background: linear-gradient(135deg,#1a237e,#3949ab); color:white; padding:24px; border-radius:12px; margin-bottom:24px; }
.api-key-display { margin-top:8px; font-size:.85em; opacity:.8; }
.api-key-display code { background:rgba(255,255,255,.15); padding:2px 8px; border-radius:4px; }
.stats-row { display:grid; grid-template-columns:repeat(4,1fr); gap:16px; margin-bottom:24px; }
.stat-card { background:white; border-radius:10px; padding:20px; text-align:center; box-shadow:0 2px 8px rgba(0,0,0,.08); }
.stat-num { font-size:2em; font-weight:bold; color:#1a237e; }
.stat-label { color:#666; font-size:.85em; margin-top:4px; }
.search-bar { margin-bottom:16px; }
.search-bar input { width:100%; padding:10px 14px; border:1px solid #ddd; border-radius:8px; font-size:1em; }
.search-results { background:white; padding:16px; border-radius:10px; margin-bottom:16px; }
.result-item { padding:8px 0; border-bottom:1px solid #f0f0f0; }
.recent-contracts { background:white; border-radius:10px; padding:20px; box-shadow:0 2px 8px rgba(0,0,0,.08); }
.recent-contracts h3 { margin-bottom:16px; color:#1a237e; }
.contract-row { display:flex; align-items:center; gap:12px; padding:10px 0; border-bottom:1px solid #f0f0f0; cursor:pointer; }
.contract-row:hover { background:#f5f5f5; }
.ct-title { flex:1; font-weight:500; }
.ct-amount { color:#388e3c; font-weight:bold; }
.badge { padding:2px 10px; border-radius:12px; font-size:.8em; font-weight:600; }
.badge-approved { background:#e8f5e9; color:#2e7d32; }
.badge-pending  { background:#fff3e0; color:#e65100; }
.badge-draft    { background:#e3f2fd; color:#1565c0; }
</style>
