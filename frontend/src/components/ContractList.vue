<template>
  <div class="page">
    <div class="page-header">
      <h2>Contracts</h2>
      <button @click="showCreate = !showCreate" class="btn-primary">+ New Contract</button>
    </div>

    <div v-if="showCreate" class="create-form card">
      <h3>Create Contract</h3>
      <input v-model="form.title"       placeholder="Title" />
      <textarea v-model="form.description" placeholder="Description"></textarea>
      <!-- VULNERABLE #21: No client-side validation for negative amount -->
      <input v-model.number="form.amount" type="number" placeholder="Amount (can be negative)" />
      <button @click="createContract" class="btn-primary">Create</button>
    </div>

    <div class="card">
      <table>
        <thead>
          <tr>
            <th>ID</th><th>Title</th><th>Amount</th><th>Status</th><th>Owner</th><th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="c in contracts" :key="c.id">
            <td>{{ c.id }}</td>
            <td>{{ c.title }}</td>
            <td :class="c.amount < 0 ? 'negative' : ''">
              ${{ c.amount?.toLocaleString() }}
              <!-- VULNERABLE #21: Negative amounts shown without warning -->
            </td>
            <td><span :class="'badge badge-' + c.status">{{ c.status }}</span></td>
            <td>{{ c.owner_id }}</td>
            <td>
              <!-- VULNERABLE #9: Any user can view any contract ID (IDOR) -->
              <button @click="$router.push('/contracts/' + c.id)" class="btn-sm">View</button>
            </td>
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
  name: 'ContractList',
  data() {
    return {
      contracts:  [],
      showCreate: false,
      form: { title: '', description: '', amount: 0 },
    }
  },
  async mounted() {
    const res = await axios.get(`${API}/api/contracts`, {
      headers: { Authorization: 'Bearer ' + localStorage.getItem('token') },
    })
    this.contracts = res.data
  },
  methods: {
    async createContract() {
      await axios.post(`${API}/api/contracts`, this.form, {
        headers: { Authorization: 'Bearer ' + localStorage.getItem('token') },
      })
      this.showCreate = false
      location.reload()
    },
  },
}
</script>

<style scoped>
.page { padding:24px; max-width:1100px; margin:0 auto; }
.page-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:20px; }
.page-header h2 { color:#1a237e; }
.card { background:white; border-radius:10px; padding:20px; box-shadow:0 2px 8px rgba(0,0,0,.08); margin-bottom:20px; }
.create-form input, .create-form textarea {
  display:block; width:100%; margin-bottom:10px; padding:8px 12px;
  border:1px solid #ddd; border-radius:6px; font-size:1em;
}
.create-form textarea { height:80px; resize:vertical; }
table { width:100%; border-collapse:collapse; }
th { text-align:left; padding:10px; background:#f5f5f5; color:#555; font-weight:600; }
td { padding:10px; border-bottom:1px solid #f0f0f0; }
.negative { color:#c62828; font-weight:bold; }
.badge { padding:2px 10px; border-radius:12px; font-size:.8em; font-weight:600; }
.badge-approved { background:#e8f5e9; color:#2e7d32; }
.badge-pending  { background:#fff3e0; color:#e65100; }
.badge-draft    { background:#e3f2fd; color:#1565c0; }
.btn-primary { background:#1a237e; color:white; border:none; padding:8px 18px; border-radius:6px; cursor:pointer; }
.btn-sm { background:#e8eaf6; color:#1a237e; border:none; padding:4px 12px; border-radius:4px; cursor:pointer; }
</style>
