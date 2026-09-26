<script setup>
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { getJSON, postJSON } from '../api'
import DropStripBar from '../components/DropStripBar.vue'
const walls = ref([]); const rolls = ref([])
// 勾选状态是墙面选择的唯一数据源，请求体 wall_ids 直接由它生成
const selectedWallIds = ref([])
const rollId = ref(1)
const out = ref(null)
const err = ref('')
const route = useRoute()
onMounted(async () => {
  walls.value = (await getJSON('/api/walls')).items.filter(w => w.data_quality === 'clean')
  rolls.value = (await getJSON('/api/rolls')).items.filter(r => r.data_quality === 'clean')
  const cleanIds = new Set(walls.value.map(w => w.id))
  const fromList = String(route.query.walls || '').split(',').map(Number).filter(id => cleanIds.has(id))
  selectedWallIds.value = fromList.length ? fromList : (walls.value.length ? [walls.value[0].id] : [])
  if (rolls.value.length) rollId.value = rolls.value[0].id
})
async function run(save) {
  err.value = ''
  if (!selectedWallIds.value.length) {
    err.value = '请至少勾选一面墙'
    return
  }
  try {
    out.value = await postJSON('/api/order-batch/estimate', {
      wall_ids: [...selectedWallIds.value],
      roll_id: rollId.value,
      save,
    })
  } catch (e) {
    out.value = null
    err.value = e.message
  }
}
</script>
<template>
  <div class="page"><h1>算卷工作台（多墙合并订卷）</h1>
  <fieldset>
    <legend>墙面（可多选，同一卷材）</legend>
    <label v-for="w in walls" :key="w.id" class="wall-pick">
      <input type="checkbox" v-model="selectedWallIds" :value="w.id" />
      {{ w.name }} · 周长 {{ w.perimeter }}m · 高 {{ w.height }}m
    </label>
  </fieldset>
  <select v-model.number="rollId"><option v-for="r in rolls" :key="r.id" :value="r.id">{{ r.name }}</option></select>
  <button @click="run(false)" :disabled="!selectedWallIds.length">试算</button>
  <button @click="run(true)" :disabled="!selectedWallIds.length">保存为一条合并记录</button>
  <p v-if="err" class="warn">{{ err }}</p>
  <div v-if="out">
    <h2>合计 <strong>{{ out.totals.rolls }} 卷</strong> · 共 {{ out.totals.drops }} 条 · {{ out.totals.wall_count }} 面墙</h2>
    <p v-if="out.run_id">已保存为记录 #{{ out.run_id }}，分墙明细随记录留档，之后修改墙面不会重算。</p>
    <table class="batch-table">
      <tr v-for="it in out.items" :key="it.wall_id">
        <td>{{ it.wall_name }}</td>
        <td>{{ it.drops }} 条</td>
        <td>每条 {{ it.drop_len_m }}m</td>
        <td><strong>{{ it.rolls }} 卷</strong></td>
        <td><DropStripBar :drops="it.drops" :drop-len="it.drop_len_m" :rolls="it.rolls" /></td>
      </tr>
    </table>
  </div>
  </div>
</template>
<style scoped>
.wall-pick { display: block; margin: 0.25rem 0; }
.batch-table td { padding: 0.25rem 0.75rem; vertical-align: top; }
</style>
