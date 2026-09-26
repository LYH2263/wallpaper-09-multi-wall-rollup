<script setup>
import { computed, onMounted, ref } from 'vue'
import { getJSON, postJSON } from '../api'
import DropStripBar from '../components/DropStripBar.vue'

const walls = ref([]); const rolls = ref([])
// selected 是勾选状态的唯一来源：复选框 v-model 与请求体 wall_ids 都取自它
const selected = ref([])
const rollId = ref(1)
const out = ref(null)
const err = ref('')

onMounted(async () => {
  walls.value = (await getJSON('/api/walls')).items.filter(w => w.data_quality === 'clean')
  rolls.value = (await getJSON('/api/rolls')).items.filter(r => r.data_quality === 'clean')
  if (rolls.value.length) rollId.value = rolls.value[0].id
})

const canRun = computed(() => selected.value.length > 0)

async function run(save) {
  err.value = ''; out.value = null
  try {
    out.value = await postJSON('/api/estimate/batch', { wall_ids: selected.value, roll_id: rollId.value, save })
  } catch (e) { err.value = String(e) }
}
</script>
<template>
  <div class="page"><h1>算卷工作台</h1>
  <fieldset class="wall-picker">
    <legend>选择墙面（可多选，合并订卷）</legend>
    <label v-for="w in walls" :key="w.id" class="wall-check">
      <input type="checkbox" v-model="selected" :value="w.id" /> {{ w.name }}（周长 {{ w.perimeter }}m）
    </label>
  </fieldset>
  <select v-model.number="rollId"><option v-for="r in rolls" :key="r.id" :value="r.id">{{ r.name }}</option></select>
  <button :disabled="!canRun" @click="run(false)">试算</button><button :disabled="!canRun" @click="run(true)">保存</button>
  <p v-if="err" class="warn">{{ err }}</p>
  <div v-if="out">
    <p><strong>合计 {{ out.rolls }} 卷</strong> · 共 {{ out.drops }} 条 · {{ out.items.length }} 面墙</p>
    <div v-for="it in out.items" :key="it.wall_id" class="wall-result">
      <p>{{ it.wall_name }}：{{ it.drops }} 条 · 每条 {{ it.drop_len_m }}m → {{ it.rolls }} 卷</p>
      <DropStripBar :drops="it.drops" :drop-len="it.drop_len_m" :rolls="it.rolls" />
    </div>
  </div>
  </div>
</template>
