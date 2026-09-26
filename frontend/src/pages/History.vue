<script setup>
import { onMounted, ref } from 'vue'
import { getJSON } from '../api'
const items = ref([])
const expanded = ref(new Set())
onMounted(async () => { items.value = (await getJSON('/api/runs')).items })
function isBatch(r) { return r.result?.kind === 'order_batch' }
function toggle(id) {
  const next = new Set(expanded.value)
  next.has(id) ? next.delete(id) : next.add(id)
  expanded.value = next
}
</script>
<template>
  <div class="page"><h1>记录</h1><ul>
  <li v-for="r in items" :key="r.id">
    <template v-if="isBatch(r)">
      <a href="#" @click.prevent="toggle(r.id)">{{ expanded.has(r.id) ? '▾' : '▸' }}</a>
      合并订卷 {{ r.result.totals.wall_count }} 面墙 · 卷材 {{ r.result.roll_name || r.roll_name }}
      → <strong>{{ r.result.totals.rolls }} 卷</strong>（{{ r.result.totals.drops }} 条）
      <span v-if="r.note"> · {{ r.note }}</span>
      <table v-if="expanded.has(r.id)" class="batch-detail">
        <tr v-for="it in r.result.items" :key="it.wall_id">
          <td>{{ it.wall_name }}</td>
          <td>周长 {{ it.perimeter }}m × 高 {{ it.height }}m（存档值）</td>
          <td>{{ it.drops }} 条</td>
          <td>{{ it.rolls }} 卷</td>
        </tr>
      </table>
    </template>
    <template v-else>{{ r.wall_name }} → {{ r.result?.rolls }} 卷</template>
  </li>
</ul></div>
</template>
<style scoped>
.batch-detail { margin: 0.25rem 0 0.5rem 1.25rem; }
.batch-detail td { padding: 0.1rem 0.75rem; }
</style>
