<template>
  <div class="page">
    <div v-if="contract" class="card">
      <div class="detail-header">
        <h2>{{ contract.title }}</h2>
        <span :class="'badge badge-' + contract.status">{{ contract.status }}</span>
      </div>

      <div class="detail-grid">
        <div><label>Contract ID</label><p>{{ contract.id }}</p></div>
        <div><label>Owner ID</label><p>{{ contract.owner_id }}</p></div>
        <div>
          <label>Amount</label>
          <!-- VULNERABLE #21: Negative amounts displayed normally -->
          <p :class="contract.amount < 0 ? 'negative' : 'amount'">${{ contract.amount?.toLocaleString() }}</p>
        </div>
        <div><label>Created</label><p>{{ contract.created_at }}</p></div>
      </div>

      <div class="description">
        <label>Description</label>
        <!-- VULNERABLE #13: DOM XSS — contract description injected into innerHTML -->
        <!-- An attacker with write access can persist XSS payload in description field -->
        <div class="desc-box" ref="descBox"></div>
      </div>

      <!-- Edit form — VULNERABLE #10 IDOR + #22 skip approval + #21 negative amount -->
      <div v-if="editing" class="edit-form">
        <h3>Edit Contract</h3>
        <input v-model="editForm.title"       placeholder="Title" />
        <textarea v-model="editForm.description" placeholder="Description"></textarea>
        <input v-model.number="editForm.amount" type="number" placeholder="Amount" />
        <!-- VULNERABLE #22: Status dropdown lets user directly set 'approved' -->
        <select v-model="editForm.status">
          <option value="draft">Draft</option>
          <option value="pending">Pending</option>
          <option value="approved">Approved</option>  <!-- Skip approval workflow -->
          <option value="rejected">Rejected</option>
        </select>
        <div class="edit-actions">
          <button @click="saveContract" class="btn-primary">Save</button>
          <button @click="editing = false" class="btn-secondary">Cancel</button>
        </div>
      </div>

      <div class="actions" v-if="!editing">
        <!-- VULNERABLE #10: Any logged-in user can edit any contract (IDOR) -->
        <button @click="startEdit" class="btn-primary">Edit Contract</button>
      </div>
    </div>

    <!-- Comments section — VULNERABLE #14 Stored XSS -->
    <div class="card" v-if="contract">
      <h3>Comments</h3>
      <div class="comments-list">
        <div v-for="c in comments" :key="c.id" class="comment">
          <div class="comment-meta">User {{ c.user_id }} · {{ c.created_at }}</div>
          <!-- VULNERABLE #14: Stored XSS — raw HTML from database rendered via v-html -->
          <div class="comment-body" v-html="c.content"></div>
        </div>
        <p v-if="!comments.length" class="no-comments">No comments yet.</p>
      </div>

      <div class="add-comment">
        <textarea
          v-model="newComment"
          placeholder="Add a comment... (HTML tags allowed)"
        ></textarea>
        <!-- VULNERABLE #14: No client-side sanitization before sending -->
        <button @click="addComment" class="btn-primary">Post Comment</button>
        <small class="hint">Tip: HTML is supported in comments</small>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

const API = 'http://localhost:50000'

export default {
  name: 'ContractDetail',
  data() {
    return {
      contract:   null,
      comments:   [],
      editing:    false,
      editForm:   {},
      newComment: '',
    }
  },
  async mounted() {
    // VULNERABLE #9: Fetches any contract ID from route — no ownership enforced
    const id = this.$route.params.id
    const res = await axios.get(`${API}/api/contracts/${id}`, {
      headers: { Authorization: 'Bearer ' + localStorage.getItem('token') },
    })
    this.contract = res.data

    // VULNERABLE #13: DOM-based XSS — description written via innerHTML
    this.$nextTick(() => {
      if (this.$refs.descBox) {
        this.$refs.descBox.innerHTML = this.contract.description || ''
      }
    })

    const cr = await axios.get(`${API}/api/comments/${id}`, {
      headers: { Authorization: 'Bearer ' + localStorage.getItem('token') },
    })
    this.comments = cr.data
  },
  methods: {
    startEdit() {
      this.editForm = { ...this.contract }
      this.editing  = true
    },
    async saveContract() {
      // VULNERABLE #10: PUT to any contract ID — no server-side ownership check
      await axios.put(
        `${API}/api/contracts/${this.contract.id}`,
        this.editForm,
        { headers: { Authorization: 'Bearer ' + localStorage.getItem('token') } },
      )
      this.editing = false
      location.reload()
    },
    async addComment() {
      if (!this.newComment.trim()) return
      // VULNERABLE #14: Raw HTML payload sent to server, stored, then rendered via v-html
      await axios.post(
        `${API}/api/comments`,
        { contract_id: this.contract.id, content: this.newComment },
        { headers: { Authorization: 'Bearer ' + localStorage.getItem('token') } },
      )
      this.newComment = ''
      location.reload()
    },
  },
}
</script>

<style scoped>
.page { padding:24px; max-width:900px; margin:0 auto; }
.card { background:white; border-radius:10px; padding:24px; box-shadow:0 2px 8px rgba(0,0,0,.08); margin-bottom:20px; }
.detail-header { display:flex; align-items:center; gap:12px; margin-bottom:20px; }
.detail-header h2 { color:#1a237e; }
.detail-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:16px; margin-bottom:20px; }
.detail-grid label { font-size:.8em; color:#888; margin-bottom:4px; display:block; }
.amount { font-size:1.2em; font-weight:bold; color:#2e7d32; }
.negative { font-size:1.2em; font-weight:bold; color:#c62828; }
.description label { font-size:.8em; color:#888; margin-bottom:8px; display:block; }
.desc-box { padding:12px; background:#f9f9f9; border-radius:6px; min-height:60px; }
.edit-form input, .edit-form textarea, .edit-form select {
  display:block; width:100%; margin-bottom:10px; padding:8px 12px;
  border:1px solid #ddd; border-radius:6px; font-size:1em;
}
.edit-form textarea { height:80px; resize:vertical; }
.edit-actions { display:flex; gap:10px; }
.actions { margin-top:16px; }
.badge { padding:2px 10px; border-radius:12px; font-size:.85em; font-weight:600; }
.badge-approved { background:#e8f5e9; color:#2e7d32; }
.badge-pending  { background:#fff3e0; color:#e65100; }
.badge-draft    { background:#e3f2fd; color:#1565c0; }
.comments-list { margin-bottom:16px; }
.comment { padding:12px 0; border-bottom:1px solid #f0f0f0; }
.comment-meta { font-size:.8em; color:#999; margin-bottom:4px; }
.comment-body { color:#333; }
.no-comments { color:#999; font-style:italic; }
.add-comment textarea {
  width:100%; height:80px; padding:10px; border:1px solid #ddd;
  border-radius:6px; font-size:1em; resize:vertical; margin-bottom:8px;
}
.hint { color:#888; font-size:.8em; }
.btn-primary   { background:#1a237e; color:white; border:none; padding:8px 18px; border-radius:6px; cursor:pointer; margin-right:8px; }
.btn-secondary { background:#e0e0e0; color:#333;  border:none; padding:8px 18px; border-radius:6px; cursor:pointer; }
</style>
