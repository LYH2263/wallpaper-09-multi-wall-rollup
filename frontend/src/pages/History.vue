<script setup>
import { onMounted, ref } from 'vue'
import { getJSON } from '../api'
const items = ref([])
onMounted(async () => { items.value = (await getJSON('/api/runs')).items })
const isBatch = (r) => Array.isArray(r.result?.items)
</script>
<template>
  <div class="page"><h1>记录</h1><ul>
    <li v-for="r in items" :key="r.id">
      <template v-if="isBatch(r)">
        多墙合并（{{ r.result.items.length }} 面墙 · {{ r.roll_name }}）→ 合计 {{ r.result.rolls }} 卷
        <details>
          <summary>分墙明细</summary>
          <ul><li v-for="it in r.result.items" :key="it.wall_id">{{ it.wall_name }}：{{ it.drops }} 条 → {{ it.rolls }} 卷</li></ul>
        </details>
      </template>
      <template v-else>{{ r.wall_name }} → {{ r.result?.rolls }} 卷</template>
    </li>
  </ul></div>
</template>
